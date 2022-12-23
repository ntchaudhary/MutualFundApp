from decimal import Decimal
from typing import Dict, Optional
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection
from mutualFundApp.src.static.constants import *
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter
from pydantic import BaseModel


purchasedFundUnits = APIRouter()
header = "localhost"


class Body(BaseModel):
    installment: float
    date = {
        'day': SIP_DATE,
        'month': CURRENT_MONTH,
        'year': CURRENT_YEAR
    }


@purchasedFundUnits.post('/purchased-fund-units/{schemeCode}')
def _handler(schemeCode: str, body: Body) -> dict:
    """calculating the monthly NAV units purchased and then inserting it into DataBase with
    date of nav and amount invested
    """

    _MF = Mftool()
    _DB_OBJ = Connection()


    date = pendulum.date(
            year=body.date['year'], month=body.date['month'], day=body.date['day'])

    try:
        if schemeCode not in SCHEME_CODE:
            raise ValueError("SCHEME_CODE_INVALID")

        if date >= pendulum.today().date():
            raise ValueError("FUTURE_DATED")

        original_data = _MF.get_scheme_historical_nav(
            schemeCode, as_Dataframe=True,
        )

        original_data.index = pd.to_datetime(
            original_data.index, infer_datetime_format=True
        )
        original_data['nav'] = pd.to_numeric(
            original_data['nav'], downcast='float'
        )

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
        
        statusCode = 200
        response = "UNITS UPDATED SUCCESSFULLY"
        
    except Exception as e:
        statusCode = 500
        response = {
            "ERROR": e.args
        }

    return formatResponse(statusCode, header, response)
