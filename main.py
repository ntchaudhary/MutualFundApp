# Add your custom dependencies directory to the system path
import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "python_additional"))

from middleware.authenticationMiddleware import AuthMiddleware
from fastapi import FastAPI
from website.urls import website
from mangum import Mangum


app = FastAPI()

# app.include_router(mutualFundApp)
app.add_middleware(AuthMiddleware)
app.include_router(website)
# app.include_router(depositeApp)


handler = Mangum(app)