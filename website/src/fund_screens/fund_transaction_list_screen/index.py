from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import pandas as pd
from mftool import Mftool

from database.dbSetupAndConnection import Connection
from utilities.auth import auth_wrapper

fundTransactionList = APIRouter()
templates = Jinja2Templates(directory="website/UI/fund_UI")


def _fund_transactions_list(schemeCode) -> dict:

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

@fundTransactionList.get('/fund-transactions-list/{schemeCode}', response_class=HTMLResponse)
def index(request: Request, user_details = Depends(auth_wrapper)):

    # api_url = f"""http://127.0.0.1:8000/mutual-fund/fund-transactions-list/{request.path_params.get('schemeCode')}"""

    response = _fund_transactions_list(request.path_params.get('schemeCode')) # requests.get(api_url)

    return templates.TemplateResponse(
        "mf_transaction_details.html", 
        {
            "request": request, 
            "body":response
        }
    )