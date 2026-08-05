import asyncio
from fastapi import APIRouter, Request, Depends
from decimal import Decimal
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from boto3.dynamodb.conditions import Key

from utilities.auth import auth_wrapper
from database.dbSetupAndConnection import Connection



from utilities.utils import calculateSumFromListOFDict, convertResponse

home = APIRouter()
templates = Jinja2Templates(directory="website/UI") 

_DB_OBJ = Connection()

async def get_total_balance(user_details):
    """Return the bank balance for that account and profile"""
    # _DB_OBJ = Connection()

    table_name = 'account_and_user_profile'
    table = _DB_OBJ.dynamodb.Table(table_name)

    await asyncio.sleep(0.000001)
    jsonData = table.query(  KeyConditionExpression = Key('account_id').eq(str(user_details['account_id'])) & Key('profile').eq(user_details['profile']) )
    await asyncio.sleep(0.000001)
    jsonData = jsonData.get('Items')[0]

    mutual_fund = float(jsonData.get('current_fund_amount', 0))
    deposit = float(jsonData.get('current_deposit_amount', 0))
    bank_balance = float(jsonData.get('bank_balance', 0))
    
    return (mutual_fund,deposit,bank_balance)

@home.get('/home', response_class=HTMLResponse)
async def index(request: Request, user_details = Depends(auth_wrapper)):

    deposit = 0
    fund = 0
    bank_balance = 0

    data = await asyncio.gather(
            get_total_balance(user_details)
        )

    fund = data[0][0]
    deposit = data[0][1]
    bank_balance = data[0][2]
    # pf_amount = data[3][1] if data[3][0] else 0
    
    gold_amount = 0
    silver_amount = 0
     
    worth = fund+deposit+(gold_amount+silver_amount)+bank_balance # +pf_amount

    from  .home_screen_static import active_data_mapping
    active_data_mapping['Mutual Funds']['amount'] = fund
    active_data_mapping['Deposits']['amount'] = deposit
    # active_data_mapping['Gold']['amount'] = gold_amount
    # active_data_mapping['Silver']['amount'] = silver_amount
    active_data_mapping['Cash Flow']['amount'] = bank_balance

    body = list(active_data_mapping.values())

    return templates.TemplateResponse(
        "home.html", 
        {
            "request": request,
            "worth":worth,
            "profile":user_details['profile'],
            "listOfInstruments" : body
        }
    )