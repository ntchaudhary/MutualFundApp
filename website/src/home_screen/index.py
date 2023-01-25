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
    deposit = 0

    response_fund = requests.get("http://127.0.0.1:8000/mutual-fund/fund-details")

    response_deposit = requests.get("http://127.0.0.1:8000/deposit/details")

    sumOfFund = calculateSumFromListOFDict(response_fund.json())

    if str(response_deposit.json().get('status')) == '200':
        sumOfDeposit = calculateSumFromListOFDict(response_deposit.json().get('body'))
        deposit = int( (sumOfDeposit("principle") + sumOfDeposit("interest_earned")) )

    fund = int(sumOfFund("balance_units_value"))
    
    worth = fund+deposit
    body = list()

    for x in listOfInstruments:
        if x.lower() == 'mutual funds':
            tmp_dct = {
            "amount": fund,
            "type": x,
            "add_new_url" : "/website/add-fund",
            "details_url" : "/website/fund-list"
        }
        if x.lower() == 'deposits':
            tmp_dct = {
            "amount": deposit,
            "type": x,
            "add_new_url" : "/website/add-deposit",
            "details_url" : "/website/deposit-list"
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
            "worth":worth,
            "listOfInstruments" : body
        }
    )