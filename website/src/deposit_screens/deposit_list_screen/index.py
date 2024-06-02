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
            for value in values['Items']:
                if user_details['profile']!=value['profile']:
                    continue
                id = value['id']
                account_number = value['account_number']
                bank = value['bank']
                note = value['note']
                depositType = value['type']
                principle = float(value['principle'])
                rate = float(value['rate'])
                freq = float(value['frequency'])
                start = pendulum.parse(value['start_date'], strict=False).date() 
                maturity = pendulum.parse(value['maturity_date'], strict=False).date() 

                if depositType == 'FD':
                    c_time = ((pendulum.today().date()-start).in_days())/365
                    time = ((maturity-start).in_months())/12

                    amount = principle*( ( 1 + ( (rate/freq)/100) )**( freq*time ) )
                    c_interest = principle*( ( 1 + ( (rate/freq)/100) )**( freq*c_time ) ) - principle

                    isMatured = "Yes" if (pendulum.today().date() >= maturity) else "No"

                    dct_resp = {
                        "id" : id,
                        "account_number":account_number,
                        "bank":bank,
                        "note":note,
                        "type": "Fixed Deposit",
                        "principle":principle,
                        "rate":rate,
                        "duration":f"{(maturity-start).in_months()} months",
                        "start_date": start.for_json(),
                        "maturity_date":maturity.for_json(),
                        "maturity_amount": round(amount,0),
                        "interest_earned": ( round(amount,0) - principle ) if (isMatured == "Yes") else round(c_interest,2),
                        "isMatured": isMatured
                    }   
                    response.append(dct_resp)

                if depositType=='RD':

                    show_time = time = (maturity-start).in_months()
                    show_c_time = c_time = (pendulum.today().date()-start).in_months() + 1 # this +1 is because we have already paid the first installment before the fist month completed

                    rd_amount=0
                    rd_current_interest = 0

                    while time>=1:
                        rd_amount += principle*( ( 1 + ( (rate/freq)/100) )**( freq*time/12 ) )
                        time -=1

                    while c_time>=1:
                        rd_current_interest += principle*( ( 1 + ( (rate/freq)/100) )**( freq*c_time/12 ) ) - principle
                        c_time -=1

                    isMatured = "Yes" if (pendulum.today().date() >= maturity) else "No"

                    dct_resp = {
                        "id" : id,
                        "note":note,
                        "account_number":account_number,
                        "bank":bank,
                        "type": "Recurring Deposit",
                        "installment": principle,
                        "principle":principle*show_c_time,
                        "rate":rate,
                        "duration":f"{show_time} months",
                        "start_date": start.for_json(),
                        "maturity_date":maturity.for_json(),
                        "maturity_amount": round(rd_amount , 0),
                        "interest_earned": (round(rd_amount , 0) - (principle*show_c_time) ) if (isMatured == "Yes") else round(rd_current_interest, 2),
                        "isMatured": isMatured
                    }   
                    response.append(dct_resp)
            else:
                status_code = 200
        else:
            raise ValueError(f'No Deposite is present in system')

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

        numberOfMatured = sum([ 1 for x in response.get('body') if x['isMatured']=='Yes' ])

        body = convertDecimal(response.get('body'))

        return templates.TemplateResponse(
            "/deposit_UI/deposit_list.html", 
            {
                "request": request, 
                "profile":user_details['profile'],
                "body":body, 
                "count": len(response.get('body')),
                "numberOfMatured":numberOfMatured,
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