from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

from website.src.utilities.utils import calculateSumFromListOFDict

depositList = APIRouter()
templates = Jinja2Templates(directory="website\\UI\\deposit_UI")


@depositList.get('/deposit-list', response_class=HTMLResponse)
def index(request: Request):

    response = requests.get("http://127.0.0.1:8000/deposit/details")

    if str(response.json().get('status')) == '200':
        calculateSum = calculateSumFromListOFDict(response.json().get('body'))

        numberOfMatured = sum([ 1 for x in response.json().get('body') if x['isMatured']=='Yes' ])

        return templates.TemplateResponse(
            "deposit_list.html", 
            {
                "request": request, 
                "body":response.json().get('body'), 
                "count": len(response.json().get('body')),
                "numberOfMatured":numberOfMatured,
                "totalPrinciple": round(calculateSum("principle"),2),
                "total_interest_earned": round(calculateSum("interest_earned"),2)
            }
        )
    else:
        return templates.TemplateResponse(
            "deposit_list.html", 
            {
                "request": request, 
                "body":response.json()
            }
        )
