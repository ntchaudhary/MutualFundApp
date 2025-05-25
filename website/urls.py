from fastapi import APIRouter

from .src.home_screen.index import home

from .src.signin_signup_screen.login import login
from .src.signin_signup_screen.logout import logout
from .src.signin_signup_screen.authCallBack import authCallBack

# from .src.signin_signup_screen.sign_up import signUP
# from .src.signin_signup_screen.sign_in import signIN
# from .src.signin_signup_screen.sign_out import signOUT
# from .src.signin_signup_screen.change_password import changePassword

from .src.fund_screens.fund_list_screen.index import fundDetails
from .src.fund_screens.fund_transaction_list_screen.index import fundTransactionList
from .src.fund_screens.fund_update_screen.index import fundUpdate
from .src.fund_screens.fund_add_screen.index import fundAdd

from .src.deposit_screens.deposit_list_screen.index import depositList
from .src.deposit_screens.deposit_add_screen.index import depositAdd

from .src.cash_flow.add_delete.index import cashFlowAddDelete
from .src.cash_flow.list.index import cashFlowList

from .src.nps.nps_add.index import addNPS
from .src.nps.nps_list.index import listNPS

website = APIRouter()

_BASE_ENDPOINT = "/website"

# website.include_router(signUP)
website.include_router(login)
website.include_router(logout)
website.include_router(authCallBack)
# website.include_router(signIN)
# website.include_router(signOUT)
# website.include_router(changePassword)

website.include_router(home, prefix=_BASE_ENDPOINT)

website.include_router(fundDetails, prefix=f"{_BASE_ENDPOINT}/fund")
website.include_router(fundTransactionList, prefix=_BASE_ENDPOINT)
website.include_router(fundUpdate, prefix=_BASE_ENDPOINT)
website.include_router(fundAdd, prefix=_BASE_ENDPOINT)

website.include_router(depositList, prefix=_BASE_ENDPOINT)
website.include_router(depositAdd, prefix=_BASE_ENDPOINT)

website.include_router(cashFlowAddDelete, prefix="/website/cashFlow")
website.include_router(cashFlowList, prefix="/website/cashFlow")

website.include_router(addNPS, prefix="/website/nps")
website.include_router(listNPS, prefix="/website/nps")