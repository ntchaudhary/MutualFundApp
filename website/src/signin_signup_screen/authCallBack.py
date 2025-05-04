from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from utilities.tokenExchange import exchange_code_for_tokens

authCallBack = APIRouter()

@authCallBack.get("/auth/callback")
async def _auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    tokens, userinfo = await exchange_code_for_tokens(code)

    response = RedirectResponse(url="/website/home")
    response.set_cookie(
        "access_token", 
        tokens["access_token"], 
        httponly=True,              # Prevents JavaScript access
        secure=True,                # Only send cookie over HTTPS
        # samesite="Strict",          # Prevent CSRF by restricting cookie to the same site
        max_age=tokens["expires_in"]
    )
    response.set_cookie(
        "id_token", 
        tokens["id_token"], 
        httponly=True, 
        max_age=tokens["expires_in"]
    )
    response.set_cookie(
        "refresh_token", 
        tokens.get("refresh_token", ""), 
        httponly=True,              # Prevents JavaScript access
        secure=True,                # Only send cookie over HTTPS
        # samesite="Strict",          # Prevent CSRF by restricting cookie to the same site
        max_age=10800
    )
    response.set_cookie(
        "account_id", 
        userinfo.get("sub", ""), 
        httponly=True,              # Prevents JavaScript access
        secure=True
    )
    response.set_cookie(
        "profile", 
        userinfo.get("preferred_username", ""), 
        httponly=True,              # Prevents JavaScript access
        secure=True
    )

    return response