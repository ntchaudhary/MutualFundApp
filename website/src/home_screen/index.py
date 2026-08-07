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

async def get_total_balance(user_details: dict):
    """Return the bank balance for that account and profile"""
    # _DB_OBJ = Connection()

    table_name = 'account_and_user_profile'
    table = _DB_OBJ.dynamodb.Table(table_name)

    
    jsonData = await asyncio.to_thread(table.query, KeyConditionExpression = Key('account_id').eq(str(user_details['account_id'])) & Key('profile').eq(user_details['profile'])  )
    jsonData = jsonData.get('Items')[0]

    mutual_fund = float(jsonData.get('current_fund_amount', 0))
    deposit = float(jsonData.get('current_deposit_amount', 0))
    bank_balance = float(jsonData.get('bank_balance', 0))
    current_etf_amount = float(jsonData.get('current_etf_amount', 0))
    current_nps_amount = float(jsonData.get('current_nps_amount', 0))
    current_pf_amount = float(jsonData.get('current_pf_amount', 0))
    
    return (mutual_fund,deposit,bank_balance,current_etf_amount,current_nps_amount,current_pf_amount)

@home.get('/home', response_class=HTMLResponse)
async def index(request: Request, user_details = Depends(auth_wrapper)):

    deposit = 0
    fund = 0
    bank_balance = 0
    pf_amount = 0
    nps = 0
    etf = 0

    data = await asyncio.gather(
            get_total_balance(user_details)
        )

    fund = data[0][0]
    deposit = data[0][1]
    bank_balance = data[0][2]
    etf = data[0][3]
    nps = data[0][4]
    pf_amount = data[0][5]
     
    worth = fund+deposit+etf+nps+bank_balance+pf_amount

    from  .home_screen_static import active_data_mapping
    active_data_mapping['Mutual Funds']['amount'] = fund
    active_data_mapping['Deposits']['amount'] = deposit
    active_data_mapping['Provident Fund']['amount'] = pf_amount
    active_data_mapping['ETF']['amount'] = etf
    active_data_mapping['NPS']['amount'] = nps
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