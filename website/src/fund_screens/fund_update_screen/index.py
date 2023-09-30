from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
import pandas as pd
import pendulum,json

from utilities.utils import MyObject
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
    """calculating the monthly NAV units purchased and then inserting it into DataBase with
    date of nav and amount invested
    """
    from mftool import Mftool
    _MF = Mftool()
    _DB_OBJ = Connection()

    table = _DB_OBJ.dynamodb.Table('account_and_user_profile')

    jsonData =  table.query(  KeyConditionExpression = Key('account_id').eq(Decimal(body.account_id)) & Key('profile').eq(body.profile) )
    jsonData = jsonData.get('Items')[0]
    SCHEME_CODE = jsonData.get('fund_owned') 


    date = pendulum.date(year=body.date['year'], month=body.date['month'], day=body.date['day'])
    id = None

    try:
        if int(schemeCode) not in SCHEME_CODE:
            raise ValueError("SCHEME_CODE_INVALID")
        else:
            table2 = _DB_OBJ.dynamodb.Table('fund_transactions_details')
            response = table2.query(
                KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}"),
                ScanIndexForward=False,  # Set to True for ascending order, False for descending order
                Limit = 1
                )
            if response["Items"]:
                id = int(response["Items"][0]["transaction_id"])+1
            else:
                id = 1

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
            tableName="fund_transactions_details",
            insertData=[{
                "fund_id":              str(schemeCode),
                "transaction_id":       id,
                "UNITS_DATE":           date.strftime('%d-%m-%Y'),
                "NUMBER_OF_UNITS":      round(units, 3),
                "AMOUNT_INVESTED":      investedAmount,
                "transaction_type":     str(body.type).title(),
                "account_id":           int(body.account_id),
                "profile":              str(body.profile)
            },],
            convert=True
        )
        response = {
            "status" : 200,
            "message": "UNITS UPDATED SUCCESSFULLY"
        }
        
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