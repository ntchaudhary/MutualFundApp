from fastapi import APIRouter

from .src.fund_screens.fund_list_screen.index import fundDetails
from .src.fund_screens.fund_transaction_list_screen.index import fundTransactionList
from .src.fund_screens.fund_update_screen.index import fundUpdate
from .src.fund_screens.fund_add_screen.index import fundAdd

from .src.deposit_screens.deposit_list_screen.index import depositList
from .src.deposit_screens.deposit_add_screen.index import depositAdd

from .src.home_screen.index import home

website = APIRouter()

_BASE_ENDPOINT = "/website"

website.include_router(home, prefix=_BASE_ENDPOINT)

website.include_router(fundDetails, prefix=_BASE_ENDPOINT)
website.include_router(fundTransactionList, prefix=_BASE_ENDPOINT)
website.include_router(fundUpdate, prefix=_BASE_ENDPOINT)
website.include_router(fundAdd, prefix=_BASE_ENDPOINT)

website.include_router(depositList, prefix=_BASE_ENDPOINT)
website.include_router(depositAdd, prefix=_BASE_ENDPOINT)