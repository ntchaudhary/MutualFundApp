from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from website.src.utilities.utils import calculateSumFromListOFDict

fund = APIRouter()
templates = Jinja2Templates(directory="website\\UI")


@fund.get('/fund', response_class=HTMLResponse)
def index(request: Request):

    return templates.TemplateResponse(
        "mf_home.html", 
        {
            "request": request
        }
    )