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
    name: str
    type: str
    principle: str
    rate: str
    compound_frequency: int
    start_date: str
    maturity_date: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        principle: str = Form(...),
        gridRadios: str = Form(...),
        rate: str = Form(...),
        freqRadios: int = Form(...),
        start_date: str = Form(...),
        maturity_date: str = Form(...)
    ):
        return cls(
            name=name,
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
            "account_id":       Decimal(user_details['account_id']), 	    # number
            "frequency":        Decimal(body.compound_frequency),			# number
            "id":               id,					                        # number
            "maturity_date":    maturity_date.for_json(),		            # string	pendulum.for_json()
            "name":             body.name,				                    # string
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


@depositAdd.get('/add-deposit', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "/deposit_UI/deposit_add.html", 
        {
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
        "name": form_data.name,
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

    return templates.TemplateResponse(
            "/deposit_UI/deposit_add.html", 
            {
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