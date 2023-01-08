from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

from website.src.utilities.utils import calculateSumFromListOFDict

home = APIRouter()
templates = Jinja2Templates(directory="website\\UI")


@home.get('/', response_class=HTMLResponse)
def index(request: Request):

    listOfInstruments = ['Mutual Funds', 'Deposits']

    response_fund = requests.get("http://127.0.0.1:8000/mutual-fund/fund-details")

    response_deposit = requests.get("http://127.0.0.1:8000/deposit/details")

    sumOfFund = calculateSumFromListOFDict(response_fund.json())
    sumOfDeposit = calculateSumFromListOFDict(response_deposit.json())

    fund = int(sumOfFund("balance_units_value"))
    deposit = int( (sumOfDeposit("principle") + sumOfDeposit("interest_earned")) )
    worth = fund+deposit
    body = list()

    for x in listOfInstruments:
        if x.lower() == 'mutual funds':
            tmp_dct = {
            "amount": f"₹ {fund:,d}",
            "type": x,
            "add_new_url" : "/website/fund",
            "details_url" : "/website/fund-details"
        }
        if x.lower() == 'deposits':
            tmp_dct = {
            "amount": f"₹ {deposit: ,d}",
            "type": x,
            "add_new_url" : "",
            "details_url" : ""
        }
        if x.lower() == '':
            pass
        if x.lower() == '':
            pass

        body.append(tmp_dct)

    

    return templates.TemplateResponse(
        "home.html", 
        {
            "request": request,
            "worth":f"₹ {worth:,d}",
            "listOfInstruments" : body
        }
    )