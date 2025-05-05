from utilities.cognito_verifier import CognitoTokenVerifier


verifier = CognitoTokenVerifier()

async def verify_access_token(token: str):
    return await verifier.verify(token)