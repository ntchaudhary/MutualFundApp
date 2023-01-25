from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pydantic import BaseModel
import pendulum

depositAdd = APIRouter()
templates = Jinja2Templates(directory="website\\UI\\deposit_UI")

class DepositBody(BaseModel):
    name: str
    type: str
    principle: float
    rate: float
    compound_frequency: int
    start_date: str
    maturity_date: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        principle: float = Form(...),
        gridRadios: str = Form(...),
        rate: float = Form(...),
        freqRadios: int = Form(...),
        start_date: str = Form(...),
        maturity_date: str = Form(...)
    ):
        return cls(
            name=name,
            type=gridRadios,
            principle=principle,
            rate=rate,
            compound_frequency = freqRadios,
            start_date=start_date,
            maturity_date=maturity_date
        )


@depositAdd.get('/add-deposit', response_class=HTMLResponse)
def get_index(request: Request):

    return templates.TemplateResponse(
        "deposit_add.html", 
        {
            "request": request,
            "show": False
        }
    )

@depositAdd.post('/add-deposit', response_class=HTMLResponse)
def post_index(request: Request, form_data: DepositBody = Depends(DepositBody.as_form)):

    start = pendulum.parse(form_data.start_date, strict=False)
    maturity = pendulum.parse(form_data.maturity_date, strict=False)

    body = {
        "name": form_data.name,
        "type": form_data.type,
        "principle": form_data.principle,
        "rate": form_data.rate,
        "compound_frequency": form_data.compound_frequency,
        "start_date": {
            'day': start.day,
            'month': start.month,
            'year': start.year
        },
        "maturity_date" : {
            'day': maturity.day,
            'month': maturity.month,
            'year': maturity.year
        }
    }

    response = requests.post("http://127.0.0.1:8000/deposit/add", json=body)

    return templates.TemplateResponse(
            "deposit_add.html", 
            {
                "request": request,
                "show": True,
                "body":response.json()
            }
        )