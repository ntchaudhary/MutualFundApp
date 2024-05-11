from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from decimal import Decimal

import json

from database.dbSetupAndConnection import Connection
from utilities.auth import auth_wrapper
from utilities.utils import convertDecimalAndGroupByYear

cashFlowList = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()


@cashFlowList.get('/list', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    table = _DB.dynamodb.Table('income_expenses')

    response = table.query(
        KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])),
        ScanIndexForward=False,  # Set to True for ascending order, False for descending order
        # Limit = 5
    )['Items']

    body = convertDecimalAndGroupByYear([x for x in response if str(x["profile"])==str(user_details["profile"])])

    return templates.TemplateResponse(
        "/cash_flow_UI/list.html", 
        {
            "request": request, 
            "profile":user_details['profile'],
            "body": body,
            "years": body.keys()
        }
    )
