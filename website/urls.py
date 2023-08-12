from fastapi import APIRouter

from .src.fund_screens.fund_list_screen.index import fundDetails
from .src.fund_screens.fund_transaction_list_screen.index import fundTransactionList
from .src.fund_screens.fund_update_screen.index import fundUpdate
from .src.fund_screens.fund_add_screen.index import fundAdd

from .src.deposit_screens.deposit_list_screen.index import depositList
from .src.deposit_screens.deposit_add_screen.index import depositAdd

from .src.home_screen.index import home

from .src.signin_signup_screen.sign_up import signUP
from .src.signin_signup_screen.sign_in import signIN
from .src.signin_signup_screen.sign_out import signOUT

website = APIRouter()

_BASE_ENDPOINT = "/website"

website.include_router(signUP)
website.include_router(signIN)
website.include_router(signOUT)

website.include_router(home, prefix=_BASE_ENDPOINT)

website.include_router(fundDetails, prefix=_BASE_ENDPOINT)
website.include_router(fundTransactionList, prefix=_BASE_ENDPOINT)
website.include_router(fundUpdate, prefix=_BASE_ENDPOINT)
website.include_router(fundAdd, prefix=_BASE_ENDPOINT)

website.include_router(depositList, prefix=_BASE_ENDPOINT)
website.include_router(depositAdd, prefix=_BASE_ENDPOINT)