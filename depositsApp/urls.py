from fastapi import APIRouter
from .src.deposit.index import deposite
from .src.deposit_details.index import depositeDetails

depositeApp = APIRouter()

_BASE_ENDPOINT = "/deposit"

depositeApp.include_router(deposite, prefix=_BASE_ENDPOINT)
depositeApp.include_router(depositeDetails, prefix=_BASE_ENDPOINT)