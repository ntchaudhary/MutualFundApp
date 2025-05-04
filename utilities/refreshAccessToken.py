import os
import httpx
from fastapi import HTTPException


async def refresh_tokens(refresh_token: str):
    token_url = f"{os.getenv("COGNITO_DOMAIN")}/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Could not refresh tokens")

    return response.json()