
import pandas as pd
from mftool import Mftool
from database.dbSetupAndConnection import Connection

from fastapi import APIRouter


fundTransactionsList = APIRouter()



@fundTransactionsList.get('/fund-transactions-list/{schemeCode}')
def _handler(schemeCode: str) -> dict:

    _MF = Mftool()
    _DB_OBJ = Connection()

    name = _MF.get_scheme_quote(code=schemeCode)


    try:
        strObj = f'''Select * from FUND_{schemeCode} ;'''
        dataframe = pd.read_sql_query(strObj, _DB_OBJ.conn)
        
        dbResponse = dataframe.sort_index(ascending=False).to_dict('records')

        response={
            "schemeName": name.get('scheme_name'),
            "list": dbResponse
        }

        
    except Exception as e:
        response = {
            "ERROR": e.args
        }

    return (response)
