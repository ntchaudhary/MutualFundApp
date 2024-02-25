from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import json

from utilities.auth import auth_wrapper
from database.dbSetupAndConnection import Connection


fundAdd = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DBObj = Connection()

with open('static/mutualFundApp/fundList.json', 'rb') as data:
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
def get(request: Request, user_details = Depends(auth_wrapper)):

    
    return templates.TemplateResponse(
        "/fund_UI/fund_add.html", 
        {
            "request": request,
            "profile":user_details['profile'],
            "body": tmp,
            "show": False
        }
    )

@fundAdd.post('/add-fund', response_class=HTMLResponse)
def add_fund(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

    from mftool import Mftool

    _MF = Mftool()

    table_name = 'account_and_user_profile'
    table = _DBObj.dynamodb.Table(table_name)
    jsonData =  table.query(  KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])) & Key('profile').eq(user_details['profile']) )
    jsonData = jsonData.get('Items')

    if form_data.key not in jsonData[0].get('fund_owned'):
        jsonData[0]['fund_owned'].append(Decimal(form_data.key))

        try:
            _DBObj.insertDynamodbRow(
                tableName=table_name,
                insertData=jsonData
            )

            x = _MF.get_scheme_quote(form_data.key)
            x['fund_id'] = x['scheme_code']
            del x['scheme_code']
            x['exitTime'] = 9
            x = json.loads(json.dumps(x))

            table2 = _DBObj.dynamodb.Table('fund_details')
            table2.put_item(Item=x)

            message = "ADDED SUCCESSFULLY"
            status = 200
        except Exception as e:
            message = e.args[0].upper()
            status = 500

    else:
        message = 'FUND ALREADY EXISTS'
        status = 400
    return templates.TemplateResponse(
        "/fund_UI/fund_add.html", 
        {
            "request": request,
            "profile":user_details['profile'],
            "body": tmp,
            "show": True,
            "message": message,
            "status": status
        }
    )