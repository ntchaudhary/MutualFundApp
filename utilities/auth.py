import jwt, hashlib
from fastapi import HTTPException, Security, Header, Cookie
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta

class AuthHandler():
    security = HTTPBearer()
    secret = '6AEE0E678A168EEAE8DF707E083A158FC23515BDD52EED77EC65B669BAA82917'

    def get_password_hash(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def verify_password(self, plain_password, hashed_password):

        if hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password:
            return True
        else:
            False

    def encode_token(self, account_id, profile):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, minutes=10),
            'iat': datetime.utcnow(),
            'sub': account_id,
            'user_name': profile
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return {'account_id':payload['sub'],
                    'profile':payload['user_name']
                    }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Session has expired')
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail='Unauthorized Access')


def auth_wrapper(token: str = Cookie(None)):
    return AuthHandler().decode_token(token)