from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from fastapi import Request

import traceback

from middleware.middlewareTokenVerifier import verify_access_token
from utilities.cognito_verifier import TokenExpiredException
from utilities.refreshAccessToken import refresh_tokens

EXEMPT_PATHS = ["/login", "/auth/callback", "/static", "/favicon.ico", "/health"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # print("accessed path : ",path)
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        access_token = request.cookies.get("access_token")
        if not access_token:
            return RedirectResponse(url="/login")  # Redirect to Cognito login

        try:
            claims = await verify_access_token(access_token)
            request.state.user = claims  # You can access this later in routes
            return await call_next(request)
        except TokenExpiredException as err:
            print("authentication middleware line 27", err)
            try:
                refresh_token = request.cookies.get("refresh_token")
                tokens = refresh_tokens(refresh_token)
                response = RedirectResponse(url=path)
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
            except Exception as err:
                print("authentication middleware line 55", err)
                print(traceback.format_exc())
                return RedirectResponse(url="/login")
        except Exception as err:
            print("authentication middleware line 58", err)
            print(traceback.format_exc())
            return RedirectResponse(url="/login")