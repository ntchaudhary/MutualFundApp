import os, httpx
from fastapi import HTTPException

COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


async def exchange_code_for_tokens(code: str):
    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    tokens =  response.json()

    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

    userinfo_headers = {
            "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(f"{COGNITO_DOMAIN}/oauth2/userInfo", headers=userinfo_headers)
    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=userinfo_response.status_code, detail=userinfo_response.text)

    userinfo = userinfo_response.json()

    return tokens, userinfo