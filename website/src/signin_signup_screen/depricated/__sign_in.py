from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse , RedirectResponse
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from utilities.auth import AuthHandler
from utilities.__userSchema import AuthDetails
from database.dbSetupAndConnection import Connection


signIN = APIRouter()
templates = Jinja2Templates(directory="website/UI")
auth_handler = AuthHandler()
conn = Connection() 
table = conn.dynamodb.Table('account_and_user_profile')

@signIN.get('/sign-in', response_class=HTMLResponse)
def signin_get(request: Request):

    return templates.TemplateResponse(
        "signin.html", 
        {
            "request": request,
            'body':{
                'err_msg': ''
            }
        }
    )


@signIN.post('/sign-in')
def signin_post(request: Request, auth_details: AuthDetails = Depends(AuthDetails.as_form)):

    auth_details.profile = str(auth_details.profile).lower()

    response = table.query(  KeyConditionExpression = Key('account_id').eq(str(auth_details.account_id)) & Key('profile').eq(auth_details.profile.lower()) )

    if response['ScannedCount'] == 0:
        return templates.TemplateResponse(
            "signin.html", 
            {
                "request": request,
                'body':{
                    'err_msg': 'Invalid account id and/or user name'
                }
            }
        )
    elif not auth_handler.verify_password(auth_details.password, response['Items'][0]['password_hash']):
        return templates.TemplateResponse(
            "signin.html", 
            {
                "request": request,
                'body':{
                    'err_msg': 'Invalid password'
                }
            }
        )
    else:
        token = auth_handler.encode_token(auth_details.account_id, auth_details.profile, request._headers.get('user-agent'), request.scope.get('client')[0])
        refresh_token = auth_handler.encode_refresh_token(auth_details.account_id, auth_details.profile, request._headers.get('user-agent'), request.scope.get('client')[0])
        response = RedirectResponse(url="/website/home", status_code=303)
        expireTime = datetime.now(timezone.utc) + timedelta(days=0, minutes=59)
        response.set_cookie(
            key="token", 
            value=token, 
            expires=expireTime, 
            httponly=True,   # Prevents JavaScript access
            secure=True,     # Only send cookie over HTTPS
            samesite="Strict"  # Prevent CSRF by restricting cookie to the same site
        )
        response.set_cookie(
            key="refresh_token", 
            value=refresh_token, 
            expires=datetime.now(timezone.utc) + timedelta(days=0, minutes=59), 
            httponly=True,   # Prevents JavaScript access
            secure=True,     # Only send cookie over HTTPS
            samesite="Strict"  # Prevent CSRF by restricting cookie to the same site
        )
        return response