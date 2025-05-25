from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from boto3.dynamodb.conditions import Key

import asyncio

from database.dbSetupAndConnection import Connection
from utilities.utils import calculateSumFromListOFDict, convertResponse
from utilities.auth import auth_wrapper


fundDetails = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB_OBJ = Connection()

async def mutual_fund_fund_details(user_details) -> list:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    # _DB_OBJ = Connection()
    response = list()

    
    table = _DB_OBJ.dynamodb.Table('fund_owned_details') # type: ignore

    await asyncio.sleep(0.000001)
    account_funds =  table.query(  KeyConditionExpression = Key('account_id').eq(str(user_details['account_id'])) )['Items']
    await asyncio.sleep(0.000001)


    try:
        for currentMarketPrice in account_funds:

            # to prevent nps funds from flowing into mutual funds
            if 'nps__' in currentMarketPrice['fund_id']:
                continue
            
            currentMarketPrice['scheme_code'] = currentMarketPrice['fund_id']
            del currentMarketPrice['fund_id']

            currentMarketPrice['exitTime'] = currentMarketPrice['exit_time']

            currentMarketPrice["balance_units_value"] = round(float(currentMarketPrice['total_units'])*float(currentMarketPrice['nav'])) # current market value of all units
            

            currentMarketPrice['invested'] = round(float( currentMarketPrice['invested'] ))

            # currentMarketPrice = _MF.calculate_balance_units_value( code=schemeCode, balance_units=dataframe.NUMBER_OF_UNITS.sum() )
            currentMarketPrice['gainLoss'] = ( currentMarketPrice['balance_units_value'] ) - float( currentMarketPrice['invested'] )

            currentMarketPrice['harvest'] = round( float(currentMarketPrice['reinvest_units'])*float(currentMarketPrice['nav']) ) - float(currentMarketPrice['reinvest_units_amount'])
                                                 
            currentMarketPrice['harvest_unit'] = round( float(currentMarketPrice['reinvest_units']), 2 ) if currentMarketPrice['harvest'] > 0 else 0

            currentMarketPrice['harvesting_amt_req'] = round( float(currentMarketPrice['reinvest_units']) * float(currentMarketPrice['nav']) )

            response.append(convertResponse(currentMarketPrice))
    except Exception as e:
        response.append({
            "message": str(e)
        })
    return response


@fundDetails.get('/list', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    response = asyncio.run(mutual_fund_fund_details(user_details)) # requests.get("http://127.0.0.1:8000/mutual-fund/fund-details")

    calculateSum = calculateSumFromListOFDict(response)

    return templates.TemplateResponse(
        "/fund_UI/mf_list.html", 
        {
            "request": request, 
            "profile":user_details['profile'],
            "body":response, 
            "count": len(response),
            "invested": round(calculateSum("invested"),2),
            "current": round(calculateSum("balance_units_value"),2),
            "totalReturn": round(calculateSum("gainLoss"),2),
            "totalharvest": round(calculateSum("harvest"),2)
        }
    )