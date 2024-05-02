from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
import pendulum, json

from database.dbSetupAndConnection import Connection
from utilities.utils import MyObject
from utilities.auth import auth_wrapper

cashFlowAddDelete = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()

class Income_Expense_Body(BaseModel):
    category: str
    other_category: Optional[str] = None
    sub_category: Optional[str] = None
    other_subcategory: Optional[str] = None
    amount: str
    note: Optional[str] = None
    expense_date: str
    income_expense: str

    @classmethod
    def as_form(
        cls,
        category: str = Form(...),
        other_category: str = Form(None),
        sub_category: str = Form(None),
        other_subcategory: str = Form(None),
        amount: str = Form(...),
        note: str = Form(None),
        expense_date: str = Form(...),
        typeRadios: str = Form(...)
    ):
        return cls(
            category=category,
            sub_category=sub_category,
            amount=amount,
            note=note,
            expense_date = expense_date,
            income_expense=typeRadios,
            other_category = other_category,
            other_subcategory = other_subcategory
        )


def _add(body, user_details):
    """ Add the new income or expense entry into database"""
    try:
        table = _DB.dynamodb.Table('income_expenses')

        expense_date = pendulum.date(year=body.expense_date['year'], month=body.expense_date['month'], day=body.expense_date['day'])

        if expense_date > pendulum.now().date():
            raise Exception("Future Dated Transaction")

        response = table.query(
            KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])),
            ScanIndexForward=False,  # Set to True for ascending order, False for descending order
            Limit = 1
        )

        print(response,str(expense_date.format('YYYY-MM-DD')))

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
        print(insert_json)
        _DB.insertDynamodbRow('income_expenses',insertData=[insert_json,])
            
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

def get_unique_categories_and_subcategories():
  """Fetches unique categories and subcategories from a DynamoDB table.

  Args:
      table_name (str): Name of the DynamoDB table containing transaction data.

  Returns:
      dict: Dictionary where category is the key and a list of subcategories is the value.
  """

  table = _DB.dynamodb.Table('income_expenses')

  # Scan the table using ProjectionExpression for efficiency
  response = table.scan(ProjectionExpression="income_expense, category, sub_category")
  items = response.get('Items', [])

  categories = {}
  income_expense_type = {}
  for item in items:
    income_expense = item.get('income_expense')
    category = item.get('category')
    sub_category = item.get('sub_category')

    if income_expense not in income_expense_type:
        income_expense_type[income_expense] = ['None of the mentioned',]
    if category not in income_expense_type[income_expense]:
        income_expense_type[income_expense].append(category)

    if category not in categories:
      categories[category] = ['no sub category',]
    if sub_category not in categories[category] and sub_category != '':
      categories[category].append(sub_category)

  return income_expense_type, categories


@cashFlowAddDelete.get('/add', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    income_expense_cat, options = get_unique_categories_and_subcategories()

    return templates.TemplateResponse(
        "/cash_flow_UI/add.html", 
        {
            "income_expense_cat": income_expense_cat,
            "options": options,
            "date": pendulum.now().date(),
            "request": request, 
            "profile":user_details['profile'],
            "show": False
        }
    )

@cashFlowAddDelete.post('/add', response_class=HTMLResponse)
def post_index(request: Request, form_data: Income_Expense_Body = Depends(Income_Expense_Body.as_form), user_details = Depends(auth_wrapper)):

    start = pendulum.parse(form_data.expense_date, strict=False)

    body = {
        "category": form_data.category if form_data.category != 'None of the mentioned' else form_data.other_category,
        "sub_category": form_data.sub_category if form_data.category != 'None of the mentioned' and form_data.other_subcategory is None else form_data.other_subcategory,
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

    income_expense_cat, options = get_unique_categories_and_subcategories()

    return templates.TemplateResponse(
        "/cash_flow_UI/add.html", 
        {
            "income_expense_cat": income_expense_cat,
            "options": options,
            "date": form_data.expense_date,
            "request": request, 
            "profile":user_details['profile'],
            "show": True,
            "body":response
            }
        )


@cashFlowAddDelete.delete('/delete/{transaction_id}')
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
