from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
import pendulum, json

from database.dbSetupAndConnection import Connection
from static.mutualFundApp.constants import MUTUAL_FUND_SQS_URL
from utilities.utils import MyObject, sendMessageToQueue
from utilities.auth import auth_wrapper

addNPS = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_DB = Connection()

categorized_schemes = {
    "SBI": {
        "SBI PENSION FUND SCHEME - CENTRAL GOVT": "SM001001",
        "SBI PENSION FUND SCHEME - STATE GOVT": "SM001002",
        "SBI PENSION FUND SCHEME E - TIER I": "SM001003",
        "SBI PENSION FUND SCHEME C - TIER I": "SM001004",
        "SBI PENSION FUND SCHEME G - TIER I": "SM001005",
        "NPS TRUST A/C-SBI PENSION FUNDS PRIVATE LIMITED- NPS LITE SCHEME - GOVT. PATTERN": "SM001009",
        "SBI PENSION FUNDS PVT LTD SCHEME - CORPORATE-CG": "SM001010",
        "NPS TRUST - A/C SBI PENSION FUND SCHEME - ATAL PENSION YOJANA (APY)": "SM001011",
        "SBI PENSION FUND SCHEME A - TIER I": "SM001012",
        "NPS TRUST - A/C SBI PENSION FUND SCHEME - APY FUND SCHEME": "SM001015",
        "NPS TRUST - A/C SBI PENSION FUND SCHEME - NPS TIER - II COMPOSITE SCHEME": "SM001016",
        "NPS TRUST A/C - SBI PENSION FUND - UPS CG SCHEME": "SM001017"
    },
    "UTI": {
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME - CENTRAL GOVT": "SM002001",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME - STATE GOVT": "SM002002",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME E - TIER I": "SM002003",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME C - TIER I": "SM002004",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME G - TIER I": "SM002005",
        "NPS TRUST- A/C - UTI PENSION FUND - NPS LITE SCHEME GOVT. PATTERN": "SM002009",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME - CORPORATE CG": "SM002010",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME - ATAL PENSION YOJANA (APY)": "SM002011",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME A - TIER I": "SM002012",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME - APY FUND SCHEME": "SM002015",
        "NPS TRUST- A/C - UTI PENSION FUND SCHEME - NPS TIER- II COMPOSITE": "SM002016",
        "NPS TRUST A/C - UTI PENSION FUND SCHEME - UPS CG SCHEME": "SM002017"
    },
    "LIC": {
        "LIC PENSION FUND SCHEME - CENTRAL GOVT": "SM003001",
        "LIC PENSION FUND SCHEME - STATE GOVT": "SM003002",
        "NPS TRUST A/C-LIC PENSION FUND LIMITED- NPS LITE SCHEME - GOVT. PATTERN": "SM003003",
        "LIC PENSION FUND LIMITED SCHEME - CORPORATE-CG": "SM003004",
        "LIC PENSION FUND SCHEME E - TIER I": "SM003005",
        "LIC PENSION FUND SCHEME C - TIER I": "SM003006",
        "LIC PENSION FUND SCHEME G - TIER I": "SM003007",
        "NPS TRUST - A/C LIC PENSION FUND SCHEME - ATAL PENSION YOJANA (APY)": "SM003011",
        "LIC PENSION FUND SCHEME A - TIER I": "SM003012",
        "NPS TRUST - A/C LIC PENSION FUND SCHEME - APY FUND SCHEME": "SM003015",
        "NPS TRUST - A/C LIC PENSION FUND SCHEME - NPS TIER - II COMPOSITE SCHEME": "SM003016",
        "NPS TRUST A/C - LIC PENSION FUND - UPS CG SCHEME": "SM003017"
    },
    "KOTAK": {
        "KOTAK PENSION FUND SCHEME E - TIER I": "SM005001",
        "KOTAK PENSION FUND SCHEME C - TIER I": "SM005002",
        "KOTAK PENSION FUND SCHEME G - TIER I": "SM005003",
        "NPS TRUST A/C-KOTAK MAHINDRA PENSION FUND LIMITED- NPS LITE SCHEME - GOVT. PATTERN": "SM005007",
        "KOTAK PENSION FUND SCHEME A - TIER I": "SM005008"
    },
    "ICICI": {
        "ICICI PRUDENTIAL PENSION FUND SCHEME E - TIER I": "SM007001",
        "ICICI PRUDENTIAL PENSION FUND SCHEME C - TIER I": "SM007002",
        "ICICI PRUDENTIAL PENSION FUND SCHEME G - TIER I": "SM007003",
        "NPS TRUST A/C-ICICI PRUDENTIAL PENSION FUNDS MANAGEMENT COMPANY LIMITED- NPS LITE SCHEME - GOVT. PATTERN": "SM007007",
        "ICICI PRUDENTIAL PENSION FUND SCHEME A - TIER I": "SM007008"
    },
    "HDFC": {
        "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I": "SM008001",
        "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I": "SM008002",
        "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I": "SM008003",
        "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME - NPS LITE SCHEME - GOVT. PATTERN": "SM008007",
        "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME A - TIER I": "SM008008"
    },
    "ADITYA BIRLA SUNLIFE": {
        "ADITYA BIRLA SUNLIFE PENSION FUND SCHEME E - TIER I": "SM010001",
        "ADITYA BIRLA SUNLIFE PENSION FUND SCHEME C - TIER I": "SM010002",
        "ADITYA BIRLA SUNLIFE PENSION FUND SCHEME G - TIER I": "SM010003",
        "ADITYA BIRLA SUNLIFE PENSION FUND SCHEME A - TIER I": "SM010004"
    },
    "TATA": {
        "TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME E - TIER I": "SM011001",
        "TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME C - TIER I": "SM011002",
        "TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME G - TIER I": "SM011003",
        "TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME A - TIER I": "SM011004"
    },
    "MAX LIFE": {
        "MAX LIFE PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I": "SM012001",
        "MAX LIFE PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I": "SM012002",
        "MAX LIFE PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I": "SM012003",
        "MAX LIFE PENSION FUND MANAGEMENT LIMITED SCHEME A - TIER I": "SM012004"
    },
    "AXIS": {
        "AXIS PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I": "SM013001",
        "AXIS PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I": "SM013002",
        "AXIS PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I": "SM013003",
        "AXIS PENSION FUND MANAGEMENT LIMITED SCHEME A - TIER I": "SM013004"
    },
    "DSP": {
        "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME E - TIER I": "SM014001",
        "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME C - TIER I": "SM014002",
        "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME G - TIER I": "SM014003",
        "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME A - TIER I": "SM014004"
    }
}


class add_nps_body(BaseModel):
    fund_house: str
    scheme_code: str
    allocation: str
    

    @classmethod
    def as_form(
        cls,
        fund_house: str = Form(...),
        scheme_code: str = Form(...),
        allocation: str = Form(...)
    ):
        return cls(
            fund_house=fund_house,
            scheme_code=scheme_code,
            allocation=allocation
        )


@addNPS.get('/add', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "/nps/add.html", 
        {   
            "fund_house": list(categorized_schemes.keys()),
            "schemes" : categorized_schemes,
            "request": request, 
            "profile":user_details['profile'],
            "show": False
        }
    )

@addNPS.post('/add', response_class=HTMLResponse)
def post_index(request: Request, form_data: add_nps_body = Depends(add_nps_body.as_form), user_details = Depends(auth_wrapper)):

    print('169 data received from page ', form_data.__dict__)

    try:

        if form_data.scheme_code == 'None' :
            raise Exception('Please select scheme from the list')
        
        table = _DB.dynamodb.Table('fund_owned_details')

        table.put_item(
              Item= {
                   "account_id": str(user_details['account_id']),
                   "fund_id": f"nps__{form_data.scheme_code}",
                   "allocation": str(form_data.allocation),
                   "exit_time": 99
              },
              ConditionExpression = 'attribute_not_exists(account_id) AND attribute_not_exists(fund_id)'
        )

        print("Successfully inserted ")
        response = {
            "status": 200,
            "message": "Successfully Inserted"
        }

        sendMessageToQueue(
            {
                'account_id':user_details['account_id'],
                'fund_id': f"nps__{form_data.scheme_code}",
                'operation': 'new'
            },
            MUTUAL_FUND_SQS_URL
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("Item with the same partition key and sort key already exists.")
            response = {
            "status": 500,
            "message": "Fund already exists"
        }
        else:
            print("Unexpected error occurred:", e)
            response = {
            "status": 500,
            "message": str(e)
        }
        
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }

    return templates.TemplateResponse(
        "/nps/add.html", 
        {
            "fund_house": list(categorized_schemes.keys()),
            "schemes" : categorized_schemes,
            "request": request, 
            "profile":user_details['profile'],
            "show": True,
            "body": response
            }
        )

# @addNPS.delete('/delete/{transaction_id}')
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
