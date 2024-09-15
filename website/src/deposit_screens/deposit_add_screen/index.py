from typing import Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from database.dbSetupAndConnection import Connection
from utilities.utils import MyObject, sendMessageToQueue
from utilities.auth import auth_wrapper
from static.depositeApp.constants import DEPOSIT_SQS_URL

import pendulum, boto3, json, decimal


depositAdd = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()

# URL of the SQS queue


class DepositBody(BaseModel):
    note: Optional[str] = None
    type: str
    account_number: str
    bank: str
    principle: str
    rate: str
    compound_frequency: int
    start_date: str
    maturity_date: str

    @classmethod
    def as_form(
        cls,
        account_number: str = Form(...),
        bank: str = Form(...),
        note: str = Form(""),
        principle: str = Form(...),
        gridRadios: str = Form(...),
        rate: str = Form(...),
        freqRadios: int = Form(...),
        start_date: str = Form(...),
        maturity_date: str = Form(...)
    ):
        return cls(
            account_number = account_number,
            bank = bank,
            note=note,
            type=gridRadios,
            principle=principle,
            rate=rate,
            compound_frequency = freqRadios,
            start_date=start_date,
            maturity_date=maturity_date
        )

def _add(body, user_details):
    """ Add the new FD or RD entry into database"""

    table = _DB.dynamodb.Table('deposits')

    start_date = pendulum.date(year=body.start_date['year'], month=body.start_date['month'], day=body.start_date['day'])
    maturity_date = pendulum.date(year=body.maturity_date['year'], month=body.maturity_date['month'], day=body.maturity_date['day'])

    try:
        response = table.query(
            KeyConditionExpression = Key('account_id').eq(decimal.Decimal(user_details['account_id'])),
            ScanIndexForward=False,  # Set to True for ascending order, False for descending order
            Limit = 1
        )

        if response["Items"]:
            id = response["Items"][0]["id"]+1
        else:
            id = 1

        amount= 0

        if body.type == 'FD':
            c_time = ((pendulum.today().date()-start_date).in_days())/365
            time = ((maturity_date-start_date).in_months())/12
            amount = float(body.principle)*( ( 1 + ( (float(body.rate)/body.compound_frequency)/100) )**( body.compound_frequency*time ) )

        elif body.type == 'RD':
            time = (maturity_date-start_date).in_months()
            c_time = (pendulum.today().date()-start_date).in_months() + 1 # this +1 is because we have already paid the first installment before the fist month completed      
            while time>=1:
                amount += float(body.principle)*( ( 1 + ( (float(body.rate)/body.compound_frequency)/100) )**( body.compound_frequency*time/12 ) )
                time -=1

        insert_json = {
                "note":             body.note,
                "account_number":   body.account_number,
                "bank":             body.bank,
                "account_id":       decimal.Decimal(user_details['account_id']), 	                                                                # number
                "frequency":        decimal.Decimal(body.compound_frequency),			                                                            # number
                "id":               id,					                                                                                            # number
                "maturity_date":    maturity_date.for_json(),		                                                                                # string	pendulum.for_json()
                "principle":        decimal.Decimal(body.principle) if body.type == 'FD' else decimal.Decimal(float(body.principle)*c_time),        # number
                "profile":          user_details["profile"],				                                                                        # string
                "rate":             decimal.Decimal(body.rate),		                                                                                # number
                "start_date":       start_date.for_json(),            		                                                                        # string	pendulum.for_json()
                "type":             body.type,		                                                                                                # string
                "duration":         (maturity_date-start_date).in_months(),                                                                         # number
                "installment":      decimal.Decimal(body.principle) if body.type == 'RD' else decimal.Decimal(),                                    # number
                "interest_earned":  decimal.Decimal(),                                                                                              # number
                "isMatured":        False,                                                                                                          # boolean
                "maturity_amount":  decimal.Decimal(str(round(amount,0) ))                                                                          # number
            }
        
        print('line 114', insert_json)

        _DB.insertDynamodbRow('deposits',insertData=[insert_json,])


        sendMessageToQueue(user_details, DEPOSIT_SQS_URL)
        
        response = {
            "status" : 200,
            "message": "DEPOSIT ADDED SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }
    print(response)

    return response


def get_unique_banks():
  """Fetches unique bank names from a DynamoDB table.

  Args:
      table_name (str): Name of the DynamoDB table containing transaction data.

  Returns:
      dict: Dictionary where category is the key and a list of subcategories is the value.
  """

  table = _DB.dynamodb.Table('deposits')

  # Scan the table using ProjectionExpression for efficiency
  response = table.scan(ProjectionExpression="bank")
  items = response.get('Items', [])

  bank = list()
  for item in items:

    bank_name = item.get('bank')
    bank.append(bank_name)

  return list(set(bank))


@depositAdd.get('/add-deposit', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    banks = get_unique_banks()

    return templates.TemplateResponse(
        "/deposit_UI/deposit_add.html", 
        {
            "banks": banks,
            "request": request, 
            "profile":user_details['profile'],
            "show": False
        }
    )

@depositAdd.post('/add-deposit', response_class=HTMLResponse)
async def post_index(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

    start = pendulum.parse(form_data.start_date, strict=False)
    maturity = pendulum.parse(form_data.maturity_date, strict=False)

    body = {
        "note": form_data.note,
        "account_number": form_data.account_number,
        "bank": form_data.bank,
        "type": form_data.type,
        "principle": form_data.principle,
        "rate": form_data.rate,
        "compound_frequency": form_data.compound_frequency,
        "start_date": {
            'day': start.day,
            'month': start.month,
            'year': start.year
        },
        "maturity_date" : {
            'day': maturity.day,
            'month': maturity.month,
            'year': maturity.year
        }
    }

    response = _add(MyObject(**body), user_details)

    banks = get_unique_banks()

    return templates.TemplateResponse(
            "/deposit_UI/deposit_add.html", 
            {
                "banks":banks,
                "request": request, 
                "profile":user_details['profile'],
                "show": True,
                "body":response
            }
        )


@depositAdd.delete('/delete/{fdID}')
def _delete(fdID: str, user_details = Depends(auth_wrapper)):
    """Delete FD or RD entry from database"""

    try:
        _DB.deleteDynamodbRow( 'deposits', {'account_id': decimal.Decimal(user_details['account_id']),'id': decimal.Decimal(fdID)} )

        sendMessageToQueue(user_details,DEPOSIT_SQS_URL)

        response = {
            "status" : 200,
            "message": "DEPOSIT DELETED SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }

    return(response)