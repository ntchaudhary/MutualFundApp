from fastapi import APIRouter

from .src.fund.fund_list_screen.index import fundDetails
from .src.fund.fund_transaction_list_screen.index import fundTransactionList

from .src.home_screen.index import home

website = APIRouter()

_BASE_ENDPOINT = "/website"

website.include_router(home, prefix=_BASE_ENDPOINT)
website.include_router(fundDetails, prefix=_BASE_ENDPOINT)
website.include_router(fundTransactionList, prefix=_BASE_ENDPOINT)