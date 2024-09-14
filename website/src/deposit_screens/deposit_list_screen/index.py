from decimal import Decimal
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import pendulum

from boto3.dynamodb.conditions import Key

from database.dbSetupAndConnection import Connection
from utilities.utils import calculateSumFromListOFDict, convertDecimal
from utilities.auth import auth_wrapper

import asyncio

depositList = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB_OBJ = Connection()


async def deposit_details(user_details) -> dict:
    """Return list of all the investment made in fixed and Recurring desposits and the amount they have made till today"""
    
    table = _DB_OBJ.dynamodb.Table('deposits')
    response = list()
    status_code = 404

    try:
        await asyncio.sleep(0.000001)
        values = table.query(  KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])) )
        await asyncio.sleep(0.000001)

        if values['Items']:
            status_code = 200
            response = values["Items"]
        else:
            raise ValueError(f'No Deposite is present in system')
        

        for row in response:
            row['isMatured'] = False if pendulum.parse(row['maturity_date'], strict=False).date() >= pendulum.today().date() else True

    except ValueError as e:
        status_code = 404
        response = {
            "message": str(e)
        }
    except Exception as e:
        status_code = 500
        response = {
            "message": str(e)
        }


    return({"status" : status_code, "body": response })


@depositList.get('/deposit-list', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    response = asyncio.run(deposit_details(user_details))

    if str(response.get('status')) == '200':
        calculateSum = calculateSumFromListOFDict(response.get('body'))

        body = convertDecimal(response.get('body'))

        return templates.TemplateResponse(
            "/deposit_UI/deposit_list.html", 
            {
                "request": request, 
                "profile":user_details['profile'],
                "body":body, 
                "count": len(response.get('body')),
                "totalPrinciple": round(calculateSum("principle"),2),
                "total_interest_earned": round(calculateSum("interest_earned"),2)
            }
        )
    else:
        return templates.TemplateResponse(
            "/deposit_UI/deposit_list.html", 
            {
                "request": request, 
                "profile":user_details['profile'],
                "body":response
            }
        )