import os
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

logout = APIRouter()

COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
LOGOUT_REDIRECT_URI = os.getenv("LOGOUT_REDIRECT_URI")  # post-logout landing page

@logout.get("/logout")
def _logout():
    cognito_logout_url = (
        f"{COGNITO_DOMAIN}/logout"
        f"?client_id={CLIENT_ID}"
        f"&logout_uri={LOGOUT_REDIRECT_URI}"
    )

    response = RedirectResponse(url=cognito_logout_url)

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("id_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("account_id")
    response.delete_cookie("profile")

    return response 

# https://https//ap-south-1xlgvj63bu.auth.ap-south-1.amazoncognito.com/logout?client_id=6franvrajter8f8eovn4jvqd9i&logout_uri=http://localhost:8000/login