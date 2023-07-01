from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from mftool import Mftool
import pandas as pd
import pendulum,json

from utilities.utils import MyObject
from utilities.auth import auth_wrapper
from database.dbSetupAndConnection import Connection


fundUpdate = APIRouter()
templates = Jinja2Templates(directory="website/UI/fund_UI")
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

    _MF = Mftool()
    _DB_OBJ = Connection()

    with open('static/mutualFundApp/Data.json', 'rb') as dataFile:
        CONSTANTS = json.load(dataFile)
    SCHEME_CODE = list(CONSTANTS.keys())


    date = pendulum.date(
            year=body.date['year'], month=body.date['month'], day=body.date['day'])

    try:
        if schemeCode not in SCHEME_CODE:
            raise ValueError("SCHEME_CODE_INVALID")

        if date >= pendulum.today().date():
            raise ValueError("FUTURE_DATED")

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

        _DB_OBJ.insertFileData(
            code=schemeCode,
            file=(date.strftime('%d-%m-%Y'), round(units, 3), body.installment)
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

def _sell(schemeCode, body):
    """Sell the Mutual Funds Units based on either on number of units or based on date purchased"""

    _DB_OBJ = Connection()
    
    with open('static/mutualFundApp/Data.json', 'rb') as dataFile:
        CONSTANTS = json.load(dataFile)
    SCHEME_CODE = list(CONSTANTS.keys())

    date = pendulum.date(year=body.date['year'], month=body.date['month'], day=body.date['day'])
    
    try:
        if schemeCode not in SCHEME_CODE:
            raise ValueError("SCHEME_CODE_INVALID")
        
        if body.units != 0:
            units = body.units
            strObj = f'''Select * from FUND_{schemeCode} WHERE TAX_HARVESTED = 'NO';'''
            original_data = pd.read_sql_query(strObj, _DB_OBJ.conn)

            original_data['UNITS_DATE'] = pd.to_datetime(original_data['UNITS_DATE'], infer_datetime_format=True, dayfirst=True)
            data1 = original_data.copy(deep=True)
            data1 = data1.set_index('UNITS_DATE')
            data1 = data1.sort_index(inplace=False)

            for x in data1.iterrows():
                tmpUnits = x[1].NUMBER_OF_UNITS

                if tmpUnits > 0:
                    units = units - tmpUnits

                if units > 0 and (tmpUnits - units) < 0:  # means all units of this row are consumed
                    _DB_OBJ.updateRows(code=schemeCode, date=x[0].strftime('%d-%m-%Y'))  # but still some sold units remains

                if units <= 0 and (tmpUnits - units) > 0:  # means all the sold units are consumed
                    print(f'this row is changed 2 \n {x[1]}')  # but row has more units then the sold units
                    print(f'remaining units are {units}\n')
                    sqlstmt = f''' UPDATE FUND_{schemeCode} SET NUMBER_OF_UNITS = {tmpUnits - units} WHERE UNITS_DATE = ? '''
                    cur = _DB_OBJ.conn.cursor()
                    cur.execute(sqlstmt, (x[0].strftime('%d-%m-%Y'),))
                    _DB_OBJ.conn.commit()
                    break

                if units == 0:  # means all the units sold are consumed by one row or multiple rows
                    _DB_OBJ.updateRows(code=schemeCode, date=x[0].strftime('%d-%m-%Y'))
                    break

        else:
            print('in elseeeeeeeeee')
            if body.date['month'] in [11,12]:
                dateStr = f"{body.date['day']}-{body.date['month']}-{body.date['year']}"
            else:
                dateStr = f"{body.date['day']}-0{body.date['month']}-{body.date['year']}"
            print(schemeCode,dateStr)
            _DB_OBJ.updateRows(code=schemeCode, date=dateStr)
        
        response = {
            "status" : 200,
            "message": "UNITS UPDATED SUCCESSFULLY"
        }
        
    except Exception as e:
        response = {
            "status" : 500,
            "ERROR": e.args
        }

    return (response)


@fundUpdate.get('/{schemeCode}/update', response_class=HTMLResponse)
def buy_get(schemeCode: str, request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "fund_update.html", 
        {
            "request": request,
            "show": False
        }
    )

@fundUpdate.post('/{schemeCode}/update', response_class=HTMLResponse)
def buy_post(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

    purchaseDate = pendulum.parse(form_data.purchaseDate, strict=False)

    body_dict = {
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
        response = _sell(request.path_params.get('schemeCode'), body) # requests.put(f"http://127.0.0.1:8000/mutual-fund/fund-transactions/{request.path_params.get('schemeCode')}/sell", json=body)

    return templates.TemplateResponse(
            "fund_update.html", 
            {
                "request": request,
                "show": True,
                "body":response
            }
        )