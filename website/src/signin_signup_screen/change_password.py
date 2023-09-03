from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from decimal import Decimal

from database.dbSetupAndConnection import Connection
from utilities.auth import auth_wrapper,AuthHandler

auth_handler = AuthHandler()
changePassword = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()
table = _DB.dynamodb.Table('account_and_user_profile')

class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @classmethod
    def as_form(
        cls,
        old_password: str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(...)
    ):
        return cls(
            old_password=old_password,
            new_password=new_password,
            confirm_password=confirm_password
        )

@changePassword.get('/change-password', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "/change_password.html", 
        {
            "request": request,
            "show": False
        }
    )

@changePassword.post('/change-password', response_class=HTMLResponse)
def post_index(request: Request, form_data: ChangePasswordBody = Depends(ChangePasswordBody.as_form), user_details = Depends(auth_wrapper)):

    jsonData =  table.query(  KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])) & Key('profile').eq(user_details['profile']) )
    jsonData = jsonData.get('Items')

    old_pass = form_data.old_password
    new_pass = form_data.new_password
    confirm_pass = form_data.confirm_password

    old_hashed_password = auth_handler.get_password_hash(old_pass)

    if old_hashed_password == jsonData[0]['password_hash']:
        if new_pass == confirm_pass:
            hashed_password = auth_handler.get_password_hash(new_pass)
            jsonData[0]['password_hash'] = hashed_password
            try:
                _DB.insertDynamodbRow(
                    tableName='account_and_user_profile',
                    insertData=jsonData
                )

                response = {
                    'status': 200,
                    'message': "Password changes successfully"
                }
            except Exception as err:
                print(err)
                response = {
                    'status': 500,
                    'message': "something went wrong"
                }
        else:
            response = {
                'status': 400,
                'message': "new & confirm password does not match"
            }
    else:
        response = {
                'status': 400,
                'message': "old password does not match"
            }

    return templates.TemplateResponse(
            "/change_password.html", 
            {
                "request": request,
                "show": True,
                "body":response
            }
        )