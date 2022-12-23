from fastapi import APIRouter
from .src.fund_details.index import fundDetails

mutualFundApp = APIRouter()

_BASE_ENDPOINT = "/mutual-fund"

mutualFundApp.include_router(fundDetails, prefix=_BASE_ENDPOINT)
