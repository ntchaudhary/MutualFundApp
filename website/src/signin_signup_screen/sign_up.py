from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import random

from utilities.auth import AuthHandler
from utilities.userSchema import AuthDetails
from database.dbSetupAndConnection import Connection


signUP = APIRouter()
templates = Jinja2Templates(directory="website/UI")
auth_handler = AuthHandler()
conn = Connection() 
table = conn.dynamodb.Table('account_and_user_profile')

@signUP.get('/sign-up', response_class=HTMLResponse)
def signup_get(request: Request):

    random_number = random.randint(1000000000, 9999999999)

    while True:
        response = table.query(  KeyConditionExpression = Key('account_id').eq(random_number) )

        if response['ScannedCount'] == 0:
            break
        else:
            random_number = random.randint(1000000000, 9999999999)

    return templates.TemplateResponse(
        "signup.html", 
        {
            "request": request,
            "body": {
                'account_id': random_number,
                'showForm': True,
                'showMsg': False
            }
        }
    )


@signUP.post('/sign-up', response_class=HTMLResponse, status_code=201)
def signup_post(request: Request, auth_details: AuthDetails = Depends(AuthDetails.as_form)):

    hashed_password = auth_handler.get_password_hash(auth_details.password)

    x = {
        "account_id": Decimal(auth_details.account_id),
        "profile": str(auth_details.profile).lower(),
        "password_hash": hashed_password,
        "bank_balance": Decimal("0"),
        "fund_owned" : []
    }

    reponse = table.put_item(Item=x)

    return templates.TemplateResponse(
            "signup.html", 
            {
                "request": request,
                "body": {
                    'account_id': auth_details.account_id,
                    'showForm': False,
                    'showMsg': True
                }
            }
        )