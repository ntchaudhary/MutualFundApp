from fastapi import APIRouter
from .src.fund.index import fund
from .src.fund_list_screen.index import fundDetails
from .src.fund_transaction_list_screen.index import fundTransactionList

website = APIRouter()

_BASE_ENDPOINT = "/website"

website.include_router(fund, prefix=_BASE_ENDPOINT)
website.include_router(fundDetails, prefix=_BASE_ENDPOINT)
website.include_router(fundTransactionList, prefix=_BASE_ENDPOINT)