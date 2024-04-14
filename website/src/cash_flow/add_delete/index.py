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

cashFlow = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()

class Income_Expense_Body(BaseModel):
    category: str
    sub_category: str
    amount: str
    note: str
    expense_date: str
    income_expense: str

    @classmethod
    def as_form(
        cls,
        category: str = Form(...),
        sub_category: str = Form(...),
        amount: str = Form(...),
        note: str = Form(...),
        expense_date: str = Form(...),
        typeRadios: int = Form(...)
    ):
        return cls(
            category=category,
            sub_category=sub_category,
            amount=amount,
            note=note,
            expense_date = expense_date,
            income_expense=typeRadios
        )


def _add(body, user_details):
    """ Add the new income or expense entry into database"""

    table = _DB.dynamodb.Table('income_expenses')

    expense_date = pendulum.date(year=body.expense_date['year'], month=body.expense_date['month'], day=body.expense_date['day'])

    response = table.query(
        KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])),
        ScanIndexForward=False,  # Set to True for ascending order, False for descending order
        Limit = 1
    )

    if response["Items"]:
        if str(expense_date.format('YYYYMMDD')) in str(response["Items"][0]["transaction_id"]):
            id = response["Items"][0]["transaction_id"]+1
        else:
            id = expense_date.format('YYYYMMDD0000')
    else:
        id = expense_date.format('YYYYMMDD0000')

    insert_json = {
        "account_id":       Decimal(user_details['account_id']),
        "transaction_id":   Decimal(id),
        "profile":          user_details["profile"],
        "expense_date":     expense_date.for_json(),
        "category":         body.category,
        "sub_category":     body.sub_category,
        "note":             body.note,
        "amount":           Decimal(str(body.amount)),
        "income_expense":   body.income_expense
    }

    _DB.insertDynamodbRow('income_expenses',insertData=[insert_json,])
    
    try:
        # print(insert_json)
        
        response = {
            "status" : 200,
            "message": "ADDED SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }
    return response


@cashFlow.get('/add', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "/cash_flow_UI/add.html", 
        {
            "request": request, 
            "profile":user_details['profile'],
            "show": False
        }
    )

@cashFlow.post('/add', response_class=HTMLResponse)
def post_index(request: Request, form_data: Income_Expense_Body = Depends(Income_Expense_Body.as_form), user_details = Depends(auth_wrapper)):

    start = pendulum.parse(form_data.expense_date, strict=False)

    body = {
        "category": form_data.category,
        "sub_category": form_data.sub_category,
        "note": form_data.note,
        "amount": form_data.amount,
        "income_expense": form_data.income_expense,
        "expense_date": {
            'day': start.day,
            'month': start.month,
            'year': start.year
        }
    }

    response = _add(MyObject(**body), user_details)

    return templates.TemplateResponse(
            "/cash_flow_UI/add.html", 
            {
                "request": request, 
                "profile":user_details['profile'],
                "show": True,
                "body":response
            }
        )


@cashFlow.delete('/delete/{transaction_id}')
def _delete(transaction_id: str, user_details = Depends(auth_wrapper)):
    """Delete FD or RD entry from database"""

    try:
        _DB.deleteDynamodbRow( 'income_expenses', {'account_id': Decimal(user_details['account_id']),'transaction_id': Decimal(transaction_id)} )

        response = {
            "status" : 200,
            "message": "TRANSACTION DELETED SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }

    return(response)





