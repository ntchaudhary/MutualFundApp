from fastapi import Request
from utilities.cognito_verifier import TokenExpiredException

def auth_wrapper(request: Request):
    account_id = request.cookies.get("account_id", None)
    profile = request.cookies.get("profile", None)

    if account_id is None or  profile is None :
            raise TokenExpiredException(status_code=401, detail="Session expired")  # Redirect to Cognito login
    return {'account_id': account_id, 'profile': profile}