from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests

from website.src.utilities.utils import calculateSumFromListOFDict

fundTransactionList = APIRouter()
templates = Jinja2Templates(directory="website\\UI")


@fundTransactionList.get('/fund-transactions-list/{schemeCode}', response_class=HTMLResponse)
def index(request: Request):
    print(request.base_url)

    api_url = f"""http://127.0.0.1:8000/mutual-fund/fund-transactions-list/{request.path_params.get('schemeCode')}"""

    response = requests.get(api_url)

    return templates.TemplateResponse(
        "mf_details.html", 
        {
            "request": request, 
            "body":response.json()
        }
    )