import jwt, hashlib
from fastapi import HTTPException, Request, Response, Cookie
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta, timezone

class TokenExpiredException(HTTPException):
    pass

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

    def encode_token(self, account_id, profile, user_agent=None, user_ip=None):
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(minutes=10),  # Short-lived token
            'iat': datetime.now(timezone.utc),
            'sub': account_id,
            'user_name': profile,
            'user_ip': user_ip,         # Bind to IP
            'user_agent': user_agent    # Bind to user-agent
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')
    
    def encode_refresh_token(self, account_id, profile, user_agent=None, user_ip=None):
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),  # Long-lived token
            'iat': datetime.now(timezone.utc),
            'sub': account_id,
            'user_name': profile,
            'user_ip': user_ip,         # Bind to IP
            'user_agent': user_agent    # Bind to user-agent
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')

    def decode_token(self, token, request: Request):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            
            # Check if the IP or user-agent in token matches the current request
            if payload.get('user_ip') and payload.get('user_ip') != request.scope.get('client')[0]:
                raise HTTPException(status_code=401, detail="Unauthorized: IP mismatch")
            if payload.get('user_agent') and payload.get('user_agent') != request._headers.get('user-agent'):
                raise HTTPException(status_code=401, detail="Unauthorized: User-Agent mismatch")
            
            return {'account_id': payload['sub'], 'profile': payload['user_name']}
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Session has expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Unauthorized Access')


def auth_wrapper(request: Request,response: Response, token: str = Cookie(None), refresh_token: str = Cookie(None)):
    if not token:
        raise TokenExpiredException(status_code=401, detail='Unauthorized Access')
    
    try:
        return AuthHandler().decode_token(token, request)
    except HTTPException as e:
        print(e)
        if e.detail == 'Session has expired' and refresh_token:
            # If access token is expired, try to refresh it using the refresh token
            try:
                refresh_data = AuthHandler().decode_token(refresh_token, request)
                # Generate a new access token and set it in the cookie
                new_access_token = AuthHandler().encode_token(refresh_data['account_id'], refresh_data['profile'], request._headers.get('user-agent'), request.scope.get('client')[0])
                response.set_cookie(key="token", value=new_access_token, expires=datetime.now(timezone.utc) + timedelta(days=0, minutes=10), httponly=True, secure=True, samesite="Lax")
                return refresh_data  # Return the refreshed token data
            except HTTPException:
                # If refresh token is also expired or invalid, redirect to login
                raise TokenExpiredException(status_code=401, detail="Token expired, login required")
        else:
            # If the token is invalid or expired, redirect to login
            raise TokenExpiredException(status_code=401, detail="Token expired, login required")
        