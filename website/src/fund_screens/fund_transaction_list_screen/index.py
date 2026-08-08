from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key

from database.dbSetupAndConnection import Connection
from utilities.auth import auth_wrapper


fundTransactionList = APIRouter()
templates = Jinja2Templates(directory="website/UI")


def _fund_transactions_list(schemeCode, user_details) -> dict:

    _DB_OBJ = Connection()
    table1 = _DB_OBJ.dynamodb.Table('fund_details')
    table2 = _DB_OBJ.dynamodb.Table('fund_transaction_details')

    name = table1.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items']

    try:
        db_data_all = table2.query(
            KeyConditionExpression = Key('account_id').eq(str(user_details['account_id']),) & Key('fund_id__id').begins_with(str(schemeCode)),
            ScanIndexForward=False
        )['Items']
        

        response={
            "schemeCode": schemeCode,
            "schemeName": name[0].get('scheme_name'),
            "list": db_data_all
        }
    except Exception as e:
        response = {
            "schemeCode": schemeCode,
            "ERROR": e.args
        }
    return (response)

@fundTransactionList.get('/{schemeCode}/transactions', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    response = _fund_transactions_list(request.path_params.get('schemeCode'), user_details) # requests.get(api_url)

    return templates.TemplateResponse(
        "/fund_UI/mf_transaction_details.html", 
        {
            "request": request,
            "profile":user_details['profile'], 
            "body":response
        }
    )