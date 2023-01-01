
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection
from mutualFundApp.src.static.constants import *
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter


fundTransactionsList = APIRouter()



@fundTransactionsList.get('/fund-transactions-list/{schemeCode}')
def _handler(schemeCode: str) -> dict:

    _MF = Mftool()
    _DB_OBJ = Connection()


    try:
        strObj = f'''Select * from FUND_{schemeCode} ;'''
        dataframe = pd.read_sql_query(strObj, _DB_OBJ.conn)
        
        response = dataframe.sort_index(ascending=False).to_dict('records')
        
    except Exception as e:
        response = {
            "ERROR": e.args
        }

    return (response)
