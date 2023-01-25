from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pydantic import BaseModel
from typing import Optional
import pendulum

fundUpdate = APIRouter()
templates = Jinja2Templates(directory="website\\UI\\fund_UI")

class DepositBody(BaseModel):
    type: str
    installment: Optional[float]
    units: Optional[float]
    purchaseDate: str

    @classmethod
    def as_form(
        cls,
        gridRadios: str = Form(...),
        installment: float = Form(...),
        units: float = Form(...),
        purchaseDate: str = Form(...)
    ):
        return cls(
            type = gridRadios,
            installment=installment,
            units=units,
            purchaseDate=purchaseDate
            )


@fundUpdate.get('/{schemeCode}/update', response_class=HTMLResponse)
def buy_get(schemeCode: str, request: Request):

    return templates.TemplateResponse(
        "fund_update.html", 
        {
            "request": request,
            "show": False
        }
    )

@fundUpdate.post('/{schemeCode}/update', response_class=HTMLResponse)
def buy_post(request: Request, form_data: DepositBody = Depends(DepositBody.as_form)):

    purchaseDate = pendulum.parse(form_data.purchaseDate, strict=False)

    body = {
        "installment": form_data.installment,
        "units": form_data.units,
        "date" : {
            'day': purchaseDate.day,
            'month': purchaseDate.month,
            'year': purchaseDate.year
        }
    }

    if form_data.type == 'buy':
        response = requests.post(f"http://127.0.0.1:8000/mutual-fund/fund-transactions/{request.path_params.get('schemeCode')}/buy", json=body)
    elif form_data.type == 'sell':
        response = requests.put(f"http://127.0.0.1:8000/mutual-fund/fund-transactions/{request.path_params.get('schemeCode')}/sell", json=body)

    return templates.TemplateResponse(
            "fund_update.html", 
            {
                "request": request,
                "show": True,
                "body":response.json()
            }
        )