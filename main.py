from fastapi import FastAPI
from fund_details.index import fundDetails

BASE_ENDPOINT = "/mutual-fund"

app = FastAPI()

app.include_router(fundDetails, prefix=BASE_ENDPOINT)