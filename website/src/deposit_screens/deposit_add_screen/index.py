from typing import Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from decimal import Decimal
import pendulum, json

from database.dbSetupAndConnection import Connection
from utilities.utils import MyObject
from utilities.auth import auth_wrapper

depositAdd = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()

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

    response = table.query(
        KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])),
        ScanIndexForward=False,  # Set to True for ascending order, False for descending order
        Limit = 1
    )

    if response["Items"]:
        id = response["Items"][0]["id"]+1
    else:
        id = 1

    
    insert_json = {
            "note": body.note,
            "account_number": body.account_number,
            "bank": body.bank,
            "account_id":       Decimal(user_details['account_id']), 	    # number
            "frequency":        Decimal(body.compound_frequency),			# number
            "id":               id,					                        # number
            "maturity_date":    maturity_date.for_json(),		            # string	pendulum.for_json()
            "principle":        Decimal(body.principle),		            # number
            "profile":          user_details["profile"],				    # string
            "rate":             Decimal(body.rate),		                    # float
            "start_date":       start_date.for_json(),            		    # string	pendulum.for_json()
            "type":             body.type		                            # string
        }

    _DB.insertDynamodbRow('deposits',insertData=[insert_json,])
    
    try:
        print(insert_json)
        
        response = {
            "status" : 200,
            "message": "DEPOSIT ADDED SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }
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
def post_index(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

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
        _DB.deleteDynamodbRow( 'deposits', {'account_id': Decimal(user_details['account_id']),'id': Decimal(fdID)} )

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