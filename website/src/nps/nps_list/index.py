
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from database.dbSetupAndConnection import Connection
from utilities.utils import calculateSumFromListOFDict, convertResponse
from utilities.auth import auth_wrapper


listNPS = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB_OBJ = Connection()

def mutual_fund_fund_details(user_details) -> list:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    # _DB_OBJ = Connection()
    response = list()

    
    table = _DB_OBJ.dynamodb.Table('fund_owned_details') # type: ignore

    account_funds =  table.query(  KeyConditionExpression = Key('account_id').eq(str(user_details['account_id'])) )['Items']

    try:
        for currentMarketPrice in account_funds:

            
            # to prevent nps funds from flowing into mutual funds
            if 'mf__' in currentMarketPrice['fund_id']:
                continue

            currentMarketPrice['scheme_code'] = currentMarketPrice['fund_id']
            del currentMarketPrice['fund_id']

            currentMarketPrice["balance_units_value"] = round(float(currentMarketPrice['total_units'])*float(currentMarketPrice['nav'])) # current market value of all units
            
            currentMarketPrice['invested'] = round(float( currentMarketPrice['invested'] ))

            currentMarketPrice['gainLoss'] = ( currentMarketPrice['balance_units_value'] ) - float( currentMarketPrice['invested'] )

            response.append(convertResponse(currentMarketPrice))
    except Exception as e:
        response.append({
            "message": str(e)
        })
    return response


@listNPS.get('/list', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    response = mutual_fund_fund_details(user_details)

    calculateSum = calculateSumFromListOFDict(response)

    return templates.TemplateResponse(
        "/nps/list.html",
        {
            "request": request, 
            "profile":user_details['profile'],
            "body":response, 
            "count": len(response),
            "invested": round(calculateSum("invested"),2),
            "current": round(calculateSum("balance_units_value"),2),
            "totalReturn": round(calculateSum("gainLoss"),2)
        }
    )