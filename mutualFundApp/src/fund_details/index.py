from decimal import Decimal
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection
from mutualFundApp.src.static.constants import *
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter

fundDetails = APIRouter()
header = "localhost"


@fundDetails.get('/fund-details')
def _handler() -> dict:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    _MF = Mftool()
    _DB_OBJ = Connection()
    response = list()

    try:
        for schemeCode in SCHEME_CODE:
            strObj = f'''Select * from FUND_{schemeCode} WHERE TAX_HARVESTED = 'NO';'''
            dataframe = pd.read_sql_query(strObj, _DB_OBJ.conn)

            currentMarketPrice = _MF.calculate_balance_units_value(
                code=schemeCode, balance_units=dataframe.NUMBER_OF_UNITS.sum())
            currentMarketPrice['gainLoss'] = Decimal(
                currentMarketPrice['balance_units_value']) - dataframe.AMOUNT_INVESTED.sum()

            currentMarketPrice['invested'] = dataframe.AMOUNT_INVESTED.sum()

            response.append(convertResponse(currentMarketPrice))
        else:
            statusCode = 200
    except Exception as e:
        statusCode = 500
        response = {
            "ERROR": e.args[0]
        }

    return formatResponse(statusCode, header, response)
