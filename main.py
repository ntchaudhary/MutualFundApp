# from dotenv import load_dotenv

from middleware.authenticationMiddleware import AuthMiddleware

# load_dotenv(override=True)

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from utilities.auth import TokenExpiredException
from website.urls import website
from mangum import Mangum


app = FastAPI()

# app.include_router(mutualFundApp)
app.add_middleware(AuthMiddleware)
app.include_router(website)
# app.include_router(depositeApp)


handler = Mangum(app)