from fastapi import FastAPI
from mutualFundApp.urls import mutualFundApp
from website.urls import website

app = FastAPI()

app.include_router(mutualFundApp)
app.include_router(website)