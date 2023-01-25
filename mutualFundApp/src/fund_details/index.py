from decimal import Decimal
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection
from mutualFundApp.src.static.constants import *
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter

fundDetails = APIRouter()
_MF = Mftool()


@fundDetails.get('/fund-details')
def _handler() -> dict:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    
    _DB_OBJ = Connection()
    response = list()

    with open('mutualFundApp\src\static\Data.json', 'rb') as dataFile:
        CONSTANTS = json.load(dataFile)
    SCHEME_CODE = list(CONSTANTS.keys())

    try:
        for schemeCode in SCHEME_CODE:
            strObj = f'''Select * from FUND_{schemeCode} WHERE TAX_HARVESTED = 'NO';'''
            dataframe = pd.read_sql_query(strObj, _DB_OBJ.conn)

            currentMarketPrice = _MF.calculate_balance_units_value( code=schemeCode, balance_units=dataframe.NUMBER_OF_UNITS.sum() )
            currentMarketPrice['gainLoss'] = Decimal( currentMarketPrice['balance_units_value'] ) - dataframe.AMOUNT_INVESTED.sum()

            currentMarketPrice['invested'] = dataframe.AMOUNT_INVESTED.sum()

            dataframe['UNITS_DATE'] = pd.to_datetime( dataframe['UNITS_DATE'], infer_datetime_format=True )
            data1 = dataframe.copy(deep=True)
            data1 = data1.set_index('UNITS_DATE')
            # data1 = data.sort_index(ascending=False, inplace=False).tail(1).index.values[0] + np.timedelta64(370, 'D')
            data1 = data1.sort_index(inplace=False)
            endDate = pendulum.today('local').subtract(years=1).date()
            data1 = data1.loc[:endDate]

            currentMarketPrice['harvest'] = calculateGainLossOnUnits(
                                                schemeCode=schemeCode,
                                                units=data1.NUMBER_OF_UNITS.sum(),
                                                investedAmount=data1.AMOUNT_INVESTED.sum()
                                            )

            response.append(convertResponse(currentMarketPrice))
    except Exception as e:
        response = {
            "message": str(e)
        }
    return response


def calculateGainLossOnUnits(schemeCode, units, investedAmount) -> Decimal:
    """calculate the return on the units of a single fund"""
    currentMarketPrice = _MF.calculate_balance_units_value(code=schemeCode, balance_units=units)
    gainLoss = Decimal( currentMarketPrice['balance_units_value'] ) - investedAmount
    return gainLoss
