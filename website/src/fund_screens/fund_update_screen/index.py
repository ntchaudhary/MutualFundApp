from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
import pandas as pd
import pendulum,json

from static.mutualFundApp.constants import MUTUAL_FUND_SQS_URL
from utilities.utils import MyObject, sendMessageToQueue
from utilities.auth import auth_wrapper
from database.dbSetupAndConnection import Connection


fundUpdate = APIRouter()
templates = Jinja2Templates(directory="website/UI")
STAMP_DUTY_PERCENT = 0.005


class DepositBody(BaseModel):
    type: str
    installment: Optional[float]
    units: Optional[float]
    purchaseDate: str

    @classmethod
    def as_form(
        cls,
        gridRadios: str = Form(...),
        installment: float = Form(...),
        units: float = Form(...),
        purchaseDate: str = Form(...)
    ):
        return cls(
            type = gridRadios,
            installment=installment,
            units=units,
            purchaseDate=purchaseDate
            )


def _buy(schemeCode, body):
    """calculating the monthly NAV units purchased and then inserting it into DataBase with date of nav and amount invested
    """
    from mftool import Mftool
    _MF = Mftool()
    _DB_OBJ = Connection()

    table = _DB_OBJ.dynamodb.Table('fund_owned_details')

    jsonData =  table.get_item(
        Key={
                'account_id': str(body.account_id),    # Partition key
                'fund_id': str(schemeCode)   # Sort key
            }
    )

    date = pendulum.date(year=body.date['year'], month=body.date['month'], day=body.date['day'])
    id = None

    try:
        if 'Item' in jsonData:
            table2 = _DB_OBJ.dynamodb.Table('fund_transaction_details')
            response = table2.query(
                KeyConditionExpression = Key('account_id').eq(str(body.account_id)) & Key('fund_id__id').begins_with(str(schemeCode)),
                ScanIndexForward=False,  # Set to True for ascending order, False for descending order
                Limit = 1
                )
            if response["Items"]:
                id = int(response["Items"][0]["fund_id__id"].split('__')[1])+1
                print('line 72 last id in system', id)
            else:
                id = 1
        else:
            raise ValueError("SCHEME_CODE_INVALID")

        if date >= pendulum.today().date():
            raise ValueError(f"FUTURE_DATED - schemeCode - {schemeCode}, date - {date}, amount - {body.installment}")

        original_data = _MF.get_scheme_historical_nav( schemeCode, as_Dataframe=True )

        original_data.index = pd.to_datetime(original_data.index, infer_datetime_format=True, dayfirst=True)
        original_data['nav'] = pd.to_numeric(original_data['nav'], downcast='float')

        while True:
            if original_data.index.__contains__(date.to_date_string()):
                break
            else:
                date = date.add(days=1)

        investedAmount = body.installment - (body.installment * STAMP_DUTY_PERCENT / 100)

        units = investedAmount / original_data.loc[date.to_date_string()].nav

        _DB_OBJ.insertDynamodbRow(
            tableName="fund_transaction_details",
            insertData=[{
                "account_id":           str(body.account_id),
                "fund_id__id":          f"{schemeCode}__{id}",
                "unit_date":            str(date.strftime('%d-%m-%Y')),
                "number_of_units":      str(round(units, 3)),
                "amount_invested":      str(investedAmount),
                "transaction_type":     str(body.type).title()
            },]
        )
        response = {
            "status" : 200,
            "message": "UNITS UPDATED SUCCESSFULLY"
        }

        sendMessageToQueue(
            {
                'account_id': str(body.account_id),
                'profile': body.profile,
                'fund_id': str(schemeCode),
                'operation': 'buy'
            },
            MUTUAL_FUND_SQS_URL
        )
        
    except Exception as e:
        response = {
            "status" : 500,
            "message": e.args
        }

    return (response)

@fundUpdate.get('/{schemeCode}/update', response_class=HTMLResponse)
async def buy_get(schemeCode: str, request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "/fund_UI/fund_update.html", 
        {
            "request": request,
            "profile":user_details['profile'],
            "show": False
        }
    )

@fundUpdate.post('/{schemeCode}/update', response_class=HTMLResponse)
async def buy_post(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

    purchaseDate = pendulum.from_format(form_data.purchaseDate, "YYYY-MM-DD")

    body_dict = {
        "type": form_data.type,
        "account_id": user_details["account_id"],
        "profile": user_details["profile"],
        "installment": form_data.installment,
        "units": form_data.units,
        "date" : {
            'day': purchaseDate.day,
            'month': purchaseDate.month,
            'year': purchaseDate.year
        }
    }

    body = MyObject(**body_dict)

    if form_data.type == 'buy':
        response = _buy(request.path_params.get('schemeCode'), body) # requests.post(f"http://127.0.0.1:8000/mutual-fund/fund-transactions/{request.path_params.get('schemeCode')}/buy", json=body)
    elif form_data.type == 'sell':
        pass

    return templates.TemplateResponse(
            "/fund_UI/fund_update.html", 
            {
                "request": request,
                "profile":user_details['profile'],
                "show": True,
                "body":response
            }
        )

@fundUpdate.delete('/{schemeCode}/sell/{transaction_id}')
async def _delete(schemeCode: str, transaction_id: str, user_details = Depends(auth_wrapper)):
    """Delete FD or RD entry from database"""

    _DB = Connection()

    try:
        _DB.deleteDynamodbRow( 'fund_transactions_details', {'fund_id': schemeCode, 'transaction_id': Decimal(transaction_id)} )

        response = {
            "status" : 200,
            "message": "UNITS SOLD SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }

    return(response)