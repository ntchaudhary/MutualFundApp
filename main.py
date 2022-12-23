from fastapi import FastAPI
from mutualFundApp.urls import mutualFundApp


app = FastAPI()

app.include_router(mutualFundApp)
