from decimal import Decimal
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection
from static.constants import *
from utilities.utils import *

from fastapi import APIRouter

fundDetails = APIRouter()


@fundDetails.get('/fund-details')
def _handler() -> dict:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    _MF = Mftool()
    _DB_OBJ = Connection()
    mapping = list()
    header = "localhost"
    try:
        for schemeCode in SCHEME_CODE:
            strObj = f'''Select * from FUND_{schemeCode} WHERE TAX_HARVESTED = 'NO';'''
            dataframe = pd.read_sql_query(strObj, _DB_OBJ.conn)

            currentMarketPrice = _MF.calculate_balance_units_value(
                code=schemeCode, balance_units=dataframe.NUMBER_OF_UNITS.sum())
            currentMarketPrice['gainLoss'] = Decimal(
                currentMarketPrice['balance_units_value']) - dataframe.AMOUNT_INVESTED.sum()

            currentMarketPrice['invested'] = dataframe.AMOUNT_INVESTED.sum()

            mapping.append(convertResponse(currentMarketPrice))
        return formatResponse(200, header, mapping)
    except Exception as e:
        statusCode = 500
        response = {
            "ERROR": e.args[0]
        }

    return formatResponse(statusCode, header, response)
