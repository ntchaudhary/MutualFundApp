# cognito_verifier.py

import os
import time
from fastapi import HTTPException
import httpx
from jose import jwt, jwk
from jose.utils import base64url_decode

class TokenExpiredException(HTTPException):
    pass

class CognitoTokenVerifier:
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self.jwks_url = os.getenv('JWKS_URL')
        self._jwks_cache = {"keys": [], "last_fetched": 0}

    async def _fetch_jwks(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url)
            response.raise_for_status()
            return response.json()["keys"]

    async def _get_cached_jwks(self):
        now = time.time()
        if self._jwks_cache["keys"] and (now - self._jwks_cache["last_fetched"] < self.cache_ttl):
            return self._jwks_cache["keys"]

        keys = await self._fetch_jwks()
        self._jwks_cache["keys"] = keys
        self._jwks_cache["last_fetched"] = now
        return keys

    async def verify(self, token: str) -> dict:
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        if not kid:
            raise Exception("Missing 'kid' in token header")

        keys = await self._get_cached_jwks()
        key = next((k for k in keys if k["kid"] == kid), None)
        if not key:
            raise Exception("Public key not found for 'kid': " + kid)

        public_key = jwk.construct(key)
        message, encoded_signature = token.rsplit(".", 1)
        decoded_signature = base64url_decode(encoded_signature.encode())

        if not public_key.verify(message.encode(), decoded_signature):
            raise Exception("Token signature verification failed")

        claims = jwt.get_unverified_claims(token)
        if claims.get("exp") < int(time.time()):
            raise TokenExpiredException("Session expired")

        return claims
