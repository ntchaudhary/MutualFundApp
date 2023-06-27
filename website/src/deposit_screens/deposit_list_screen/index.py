from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from website.src.home_screen.index import deposit_details

from utilities.utils import calculateSumFromListOFDict

depositList = APIRouter()
templates = Jinja2Templates(directory="website/UI/deposit_UI")


@depositList.get('/deposit-list', response_class=HTMLResponse)
def index(request: Request):

    response = deposit_details()

    if str(response.get('status')) == '200':
        calculateSum = calculateSumFromListOFDict(response.get('body'))

        numberOfMatured = sum([ 1 for x in response.get('body') if x['isMatured']=='Yes' ])

        return templates.TemplateResponse(
            "deposit_list.html", 
            {
                "request": request, 
                "body":response.get('body'), 
                "count": len(response.get('body')),
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
                "body":response
            }
        )