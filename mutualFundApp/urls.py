from fastapi import APIRouter
from .src.fund_details.index import fundDetails
from .src.available_fund_list.index import availableFundList
from .src.purchased_fund_units.index import purchasedFundUnits

mutualFundApp = APIRouter()

_BASE_ENDPOINT = "/mutual-fund"

mutualFundApp.include_router(fundDetails, prefix=_BASE_ENDPOINT)
mutualFundApp.include_router(availableFundList, prefix=_BASE_ENDPOINT)
mutualFundApp.include_router(purchasedFundUnits, prefix=_BASE_ENDPOINT)