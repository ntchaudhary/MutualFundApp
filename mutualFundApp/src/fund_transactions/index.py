from typing import Optional
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection
from mutualFundApp.src.static.constants import *
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter
from pydantic import BaseModel


fundTransactions = APIRouter()


class Body(BaseModel):
    installment: Optional[float]
    units: Optional[float]
    date = {
        'day': SIP_DATE,
        'month': CURRENT_MONTH,
        'year': CURRENT_YEAR
    }


@fundTransactions.post('/fund-transactions/{schemeCode}/buy')
def _buy(schemeCode: str, body: Body):
    """calculating the monthly NAV units purchased and then inserting it into DataBase with
    date of nav and amount invested
    """

    _MF = Mftool()
    _DB_OBJ = Connection()

    with open('mutualFundApp\src\static\Data.json', 'rb') as dataFile:
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

        original_data.index = pd.to_datetime(original_data.index, infer_datetime_format=True)
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

@fundTransactions.put('/fund-transactions/{schemeCode}/sell')
def _sell(schemeCode: str, body: Body):
    """Sell the Mutual Funds Units based on either on number of units or based on date purchased"""

    _DB_OBJ = Connection()
    
    with open('mutualFundApp\src\static\Data.json', 'rb') as dataFile:
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

            original_data['UNITS_DATE'] = pd.to_datetime(original_data['UNITS_DATE'], infer_datetime_format=True)
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