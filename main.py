from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
# from mutualFundApp.urls import mutualFundApp
from utilities.auth import TokenExpiredException
from website.urls import website
# from depositsApp.urls import depositeApp
from mangum import Mangum

app = FastAPI()

# app.include_router(mutualFundApp)
app.include_router(website)
# app.include_router(depositeApp)



# Exception handler for TokenExpiredException to trigger redirection
@app.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: TokenExpiredException):
    # Redirect user to sign-in page if token is expired or invalid
    return RedirectResponse(url="/sign-in")


handler = Mangum(app)