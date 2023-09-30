from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
import pandas as pd

from database.dbSetupAndConnection import Connection
from utilities.auth import auth_wrapper

from pprint import pprint

fundTransactionList = APIRouter()
templates = Jinja2Templates(directory="website/UI")


def _fund_transactions_list(schemeCode, user_details) -> dict:

    _DB_OBJ = Connection()
    table1 = _DB_OBJ.dynamodb.Table('fund_details')
    table2 = _DB_OBJ.dynamodb.Table('fund_transactions_details')

    name = table1.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items']

    try:
        db_data_all = table2.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items']
        db_data = [x for x in db_data_all if str(x["account_id"])==str(user_details["account_id"]) and str(x["profile"])==str(user_details["profile"])]
        
        dataframe = pd.DataFrame(db_data)
        dataframe['UNITS_DATE'] = pd.to_datetime( dataframe['UNITS_DATE'], infer_datetime_format=True, dayfirst=True )
        dbResponse = dataframe.sort_values(by=['UNITS_DATE'],ascending=False).to_dict('records')

        response={
            "schemeCode": schemeCode,
            "schemeName": name[0].get('scheme_name'),
            "list": dbResponse
        }
    except Exception as e:
        response = {
            "ERROR": e.args
        }
    return (response)

@fundTransactionList.get('/fund-transactions-list/{schemeCode}', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    # api_url = f"""http://127.0.0.1:8000/mutual-fund/fund-transactions-list/{request.path_params.get('schemeCode')}"""

    response = _fund_transactions_list(request.path_params.get('schemeCode'), user_details) # requests.get(api_url)

    return templates.TemplateResponse(
        "/fund_UI/mf_transaction_details.html", 
        {
            "request": request,
            "profile":user_details['profile'], 
            "body":response
        }
    )