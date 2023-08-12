from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from website.src.home_screen.index import mutual_fund_fund_details
from utilities.utils import calculateSumFromListOFDict
from utilities.auth import auth_wrapper

import asyncio

fundDetails = APIRouter()
templates = Jinja2Templates(directory="website/UI")


@fundDetails.get('/fund-list', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    response = asyncio.run(mutual_fund_fund_details(user_details)) # requests.get("http://127.0.0.1:8000/mutual-fund/fund-details")

    calculateSum = calculateSumFromListOFDict(response)

    return templates.TemplateResponse(
        "/fund_UI/mf_list.html", 
        {
            "request": request, 
            "profile":user_details['profile'],
            "body":response, 
            "count": len(response),
            "invested": round(calculateSum("invested"),2),
            "current": round(calculateSum("balance_units_value"),2),
            "totalReturn": round(calculateSum("gainLoss"),2),
            "totalharvest": round(calculateSum("harvest"),2)
        }
    )