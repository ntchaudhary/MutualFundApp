from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from botocore.exceptions import ClientError
from static.mutualFundApp.constants import MUTUAL_FUND_SQS_URL
from utilities.auth import auth_wrapper
from database.dbSetupAndConnection import Connection
from utilities.utils import sendMessageToQueue

import json, asyncio

fundAdd = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DBObj = Connection()



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


@fundAdd.get('/add', response_class=HTMLResponse)
def get(request: Request, user_details = Depends(auth_wrapper)):

    with open('static/mutualFundApp/fundList.json', 'rb') as data:
        jsonData11 = json.load(data)

        tmp = [ {'key':x[0], 'value': x[1]} for x in jsonData11.items() ]

        tmp = sorted(tmp, key=lambda d: d['value']) 

    
    return templates.TemplateResponse(
        "/fund_UI/fund_add.html", 
        {
            "request": request,
            "profile":user_details['profile'],
            "body": tmp,
            "show": False
        }
    )

@fundAdd.post('/add', response_class=HTMLResponse)
async def add_fund(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

    try:

        with open('static/mutualFundApp/fundList.json', 'rb') as data:
            jsonData11 = await json.load(data)

            tmp = [ {'key':x[0], 'value': x[1]} for x in jsonData11.items() ]

            tmp = sorted(tmp, key=lambda d: d['value']) 

        if form_data.key == 'None' :
            raise Exception('Please select fund from the list')
        
        table = _DBObj.dynamodb.Table('fund_owned_details') # type: ignore

        table.put_item(
              Item= {
                   "account_id": str(user_details['account_id']),
                   "fund_id": f"mf__{form_data.key}",
                   "scheme_name": jsonData11[form_data.key],
                   "nav": '0',
                   "exit_time": '99',
                   "reinvest_units" : '0', 
                   "reinvest_units_amount" : '0', 
                   "invested" : '0', 
                   "total_units" :'0'
            
              },
              ConditionExpression = 'attribute_not_exists(account_id) AND attribute_not_exists(fund_id)'
        )

        message = 'Successfully Added'
        status = 200

        await asyncio.to_thread( 
            sendMessageToQueue,
            {
                'account_id':user_details['account_id'],
                'profile':user_details['profile'],
                'fund_id': f"mf__{form_data.key}",
                'operation': 'new'
            },
            MUTUAL_FUND_SQS_URL
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("Item with the same partition key and sort key already exists.")
            message = 'FUND ALREADY EXISTS'
            status = 500
        else:
            print("Unexpected error occurred:", e)
            message = e
            status = 500
        
    except Exception as e:
        message = e.args[0]
        status = 500

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