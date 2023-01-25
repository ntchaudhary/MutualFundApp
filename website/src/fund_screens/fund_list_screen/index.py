from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

from website.src.utilities.utils import calculateSumFromListOFDict

fundDetails = APIRouter()
templates = Jinja2Templates(directory="website\\UI\\fund_UI")


@fundDetails.get('/fund-list', response_class=HTMLResponse)
def index(request: Request):

    response = requests.get("http://127.0.0.1:8000/mutual-fund/fund-details")

    calculateSum = calculateSumFromListOFDict(response.json())

    return templates.TemplateResponse(
        "mf_list.html", 
        {
            "request": request, 
            "body":response.json(), 
            "count": len(response.json()),
            "invested": round(calculateSum("invested"),2),
            "current": round(calculateSum("balance_units_value"),2),
            "totalReturn": round(calculateSum("gainLoss"),2),
            "totalharvest": round(calculateSum("harvest"),2)
        }
    )