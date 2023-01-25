from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from pydantic import BaseModel
from database.dbSetupAndConnection import Connection
import json

fundAdd = APIRouter()
templates = Jinja2Templates(directory="website\\UI\\fund_UI")

with open('mutualFundApp\\src\\static\\fundList.json', 'rb') as data:
        jsonData11 = json.load(data)

tmp = [ {'key':x[0], 'value': x[1]} for x in jsonData11.items() 
                if 
                'regular' not in x[1].lower() and 
                'day' not in x[1].lower() and 
                'interval' not in x[1].lower() and 
                'series' not in x[1].lower() and 
                'fixed' not in x[1].lower() and 
                'protection' not in x[1].lower() and 
                'dividend' not in x[1].lower() and 
                'fmp' not in x[1].lower() and 
                'idcw' not in x[1].lower() and 
                'distribution' not in x[1].lower()
                ]
tmp = sorted(tmp, key=lambda d: d['value']) 


class DepositBody(BaseModel):
    key: str

    @classmethod
    def as_form(
        cls,
        fundlist: str = Form(...)
    ):
        return cls(
            key = fundlist         
            )


@fundAdd.get('/add-fund', response_class=HTMLResponse)
def get(request: Request):

    
    return templates.TemplateResponse(
        "fund_add.html", 
        {
            "request": request,
            "body": tmp,
            "show": False
        }
    )

@fundAdd.post('/add-fund', response_class=HTMLResponse)
def buy_post(request: Request, form_data: DepositBody = Depends(DepositBody.as_form)):

    print(form_data)
    with open('mutualFundApp\\src\\static\\Data.json', 'rb') as data:
        jsonData = json.load(data)

    if form_data.key not in jsonData.keys():
        jsonData[form_data.key] = [jsonData11.get(form_data.key), 0.0, ]

        with open('mutualFundApp\\src\\static\\Data.json', 'w') as newData:
            json.dump(jsonData, newData)

        try:
            Connection().createFundTable(form_data.key)
            message = "ADDED SUCCESSFULLY"
            status = 200
        except Exception as e:
            message = e.args[0].upper()
            status = 500

    else:
        message = 'FUND ALREADY EXISTS'
        status = 400
    return templates.TemplateResponse(
        "fund_add.html", 
        {
            "request": request,
            "body": tmp,
            "show": True,
            "message": message,
            "status": status
        }
    )