import os
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

login = APIRouter()

COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


@login.get("/login")
def _login():
    cognito_login_url = (
        f"{COGNITO_DOMAIN}/login"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid+profile"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(url=cognito_login_url)