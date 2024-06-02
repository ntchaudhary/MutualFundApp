from decimal import Decimal
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from boto3.dynamodb.conditions import Key

import pandas as pd
import asyncio, pendulum

from database.dbSetupAndConnection import Connection
from utilities.utils import calculateSumFromListOFDict, convertResponse
from utilities.auth import auth_wrapper


fundDetails = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB_OBJ = Connection()

async def mutual_fund_fund_details(user_details) -> dict:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    # _DB_OBJ = Connection()
    response = list()

    table = _DB_OBJ.dynamodb.Table('account_and_user_profile')
    table2 = _DB_OBJ.dynamodb.Table('fund_details')
    table3 = _DB_OBJ.dynamodb.Table('fund_transactions_details')

    await asyncio.sleep(0.000001)
    jsonData =  table.query(  KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])) & Key('profile').eq(user_details['profile']) )
    await asyncio.sleep(0.000001)
    jsonData = jsonData.get('Items')[0]
    SCHEME_CODE = jsonData.get('fund_owned') 

    try:
        for schemeCode in SCHEME_CODE:

            await asyncio.sleep(0.000001)
            db_data_all = table3.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items']
            currentMarketPrice = table2.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items'][0]
            db_data = [x for x in db_data_all if str(x["account_id"])==str(user_details["account_id"]) and str(x["profile"])==str(user_details["profile"])]
            if not db_data:
                db_data.append({'AMOUNT_INVESTED': Decimal('0.0'),
                'NUMBER_OF_UNITS': Decimal('0.0'),
                'UNITS_DATE': '31-01-2022'})
            dataframe = pd.DataFrame(db_data)
            
            await asyncio.sleep(0.000001)
            
            currentMarketPrice['scheme_code'] = currentMarketPrice['fund_id']
            del currentMarketPrice['fund_id']

            market_value = round(float(dataframe.NUMBER_OF_UNITS.sum())*float(currentMarketPrice['nav'])) # current market value of all units
            currentMarketPrice["balance_units_value"] = market_value

            # currentMarketPrice = _MF.calculate_balance_units_value( code=schemeCode, balance_units=dataframe.NUMBER_OF_UNITS.sum() )
            currentMarketPrice['gainLoss'] = Decimal( currentMarketPrice['balance_units_value'] ) - dataframe.AMOUNT_INVESTED.sum()

            currentMarketPrice['invested'] = round(dataframe.AMOUNT_INVESTED.sum())

            dataframe['UNITS_DATE'] = pd.to_datetime( dataframe['UNITS_DATE'], infer_datetime_format=True, dayfirst=True )
            data1 = dataframe.copy(deep=True)
            data1 = data1.set_index('UNITS_DATE')
            # data1 = data.sort_index(ascending=False, inplace=False).tail(1).index.values[0] + np.timedelta64(370, 'D')
            data1 = data1.sort_index(inplace=False)
            # endDate = pendulum.today('local').subtract(years=1).date()
            endDate = pendulum.today('local').subtract(years=currentMarketPrice.get('exitTime', 9999)).date()
            data1 = data1.loc[:endDate]

            currentMarketPrice['harvest'] = round( float(data1.NUMBER_OF_UNITS.sum())*float(currentMarketPrice['nav']) ) - data1.AMOUNT_INVESTED.sum()
            
            # currentMarketPrice['harvest'] = calculateGainLossOnUnits(
            #                                     schemeCode=schemeCode,
            #                                     units=data1.NUMBER_OF_UNITS.sum(),
            #                                     investedAmount=data1.AMOUNT_INVESTED.sum()
            #                                 )
                                            
            currentMarketPrice['harvest_unit'] = round( data1.NUMBER_OF_UNITS.sum(), 2 ) if currentMarketPrice['harvest'] > 0 else 0

            currentMarketPrice['harvesting_amt_req'] = round( float(data1.NUMBER_OF_UNITS.sum())*float(currentMarketPrice['nav']) )

            response.append(convertResponse(currentMarketPrice))
    except Exception as e:
        response = {
            "message": str(e)
        }
    return response


@fundDetails.get('/fund-list', response_class=HTMLResponse)
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