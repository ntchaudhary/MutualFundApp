from fastapi import APIRouter, Request
from mftool import Mftool
from decimal import Decimal
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database.dbSetupAndConnection import Connection

import pandas as pd
import json, pendulum

from utilities.utils import calculateSumFromListOFDict, convertResponse

home = APIRouter()
templates = Jinja2Templates(directory="website/UI")

_MF = Mftool()

def deposit_details() -> dict:
    """Return list of all the investment made in fixed and Recurring desposits and the amount they have made till today"""
    _DB_OBJ = Connection()
    response = list()
    status_code = 404
    existsCheck = f''' select ID, NAME, TYPE, PRINCIPLE, RATE, FREQ, START_DATE, MATURITY_DATE from DEPOSIT '''

    try:
        cur = _DB_OBJ.conn.cursor() 
        
        values = cur.execute(existsCheck).fetchall()

        if values:
            for value in values:
                id = value[0]
                name = ' '.join((value[1]).split('_'))
                depositType = value[2]
                principle = value[3]
                rate = value[4]
                freq = value[5]
                start = pendulum.parse(value[6], strict=False).date() 
                maturity = pendulum.parse(value[7], strict=False).date() 

                if depositType == 'FD':
                    c_time = ((pendulum.today().date()-start).in_days())/365
                    time = ((maturity-start).in_months())/12

                    amount = principle*( ( 1 + ( (rate/freq)/100) )**( freq*time ) )
                    c_interest = principle*( ( 1 + ( (rate/freq)/100) )**( freq*c_time ) ) - principle

                    isMatured = "Yes" if (pendulum.today().date() >= maturity) else "No"

                    dct_resp = {
                        "id" : id,
                        "name":name.title(),
                        "type": "Fixed Deposit",
                        "principle":principle,
                        "rate":rate,
                        "duration":f"{(maturity-start).in_months()} months",
                        "start_date": start,
                        "maturity_date":maturity,
                        "maturity_amount": round(amount,0),
                        "interest_earned": ( round(amount,0) - principle ) if (isMatured == "Yes") else round(c_interest,2),
                        "isMatured": isMatured
                    }   
                    response.append(dct_resp)

                if depositType=='RD':

                    show_time = time = (maturity-start).in_months()
                    show_c_time = c_time = (pendulum.today().date()-start).in_months() + 1 # this +1 is because we have already paid the first installment before the fist month completed

                    rd_amount=0
                    rd_current_interest = 0

                    while time>=1:
                        rd_amount += principle*( ( 1 + ( (rate/freq)/100) )**( freq*time/12 ) )
                        time -=1

                    while c_time>=1:
                        rd_current_interest += principle*( ( 1 + ( (rate/freq)/100) )**( freq*c_time/12 ) ) - principle
                        c_time -=1

                    isMatured = "Yes" if (pendulum.today().date() >= maturity) else "No"

                    dct_resp = {
                        "id" : id,
                        "name":name,
                        "type": "Recurring Deposit",
                        "installment": principle,
                        "principle":principle*show_c_time,
                        "rate":rate,
                        "duration":f"{show_time} months",
                        "start_date": start,
                        "maturity_date":maturity,
                        "maturity_amount": round(rd_amount , 0),
                        "interest_earned": (round(rd_amount , 0) - (principle*show_c_time) ) if (isMatured == "Yes") else round(rd_current_interest, 2),
                        "isMatured": isMatured
                    }   
                    response.append(dct_resp)
            else:
                status_code = 200
        else:
            raise ValueError(f'No Deposite is present in system')

    except ValueError as e:
        status_code = 404
        response = {
            "message": str(e)
        }
    except Exception as e:
        status_code = 500
        response = {
            "message": str(e)
        }


    return({"status" : status_code, "body": response })

def mutual_fund_fund_details() -> dict:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    _DB_OBJ = Connection()
    response = list()

    with open('static/mutualFundApp/Data.json', 'rb') as dataFile:
        CONSTANTS = json.load(dataFile)
    SCHEME_CODE = list(CONSTANTS.keys())

    try:
        for schemeCode in SCHEME_CODE:
            strObj = f'''Select * from FUND_{schemeCode} WHERE TAX_HARVESTED = 'NO';'''
            dataframe = pd.read_sql_query(strObj, _DB_OBJ.conn)

            currentMarketPrice = _MF.calculate_balance_units_value( code=schemeCode, balance_units=dataframe.NUMBER_OF_UNITS.sum() )
            currentMarketPrice['gainLoss'] = Decimal( currentMarketPrice['balance_units_value'] ) - dataframe.AMOUNT_INVESTED.sum()

            currentMarketPrice['invested'] = dataframe.AMOUNT_INVESTED.sum()

            dataframe['UNITS_DATE'] = pd.to_datetime( dataframe['UNITS_DATE'], infer_datetime_format=True, dayfirst=True )
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
                                            
            currentMarketPrice['harvest_unit'] = round( data1.NUMBER_OF_UNITS.sum(), 2 ) if currentMarketPrice['harvest'] > 0 else 0

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


@home.get('/home', response_class=HTMLResponse)
def index(request: Request):

    listOfInstruments = ['Mutual Funds', 'Deposits', 'Provident Fund', 'Gold']
    deposit = 0

    excel_data_df = pd.read_excel('database/PF_BOOK.xlsx', sheet_name='total')
    pf_amount = excel_data_df.at[4,'Values']

    response_fund = mutual_fund_fund_details()         # requests.get("http://127.0.0.1:8000/mutual-fund/fund-details")

    response_deposit = deposit_details()               # requests.get("http://127.0.0.1:8000/deposit/details")

    sumOfFund = calculateSumFromListOFDict(response_fund)

    if str(response_deposit.get('status')) == '200':
        sumOfDeposit = calculateSumFromListOFDict(response_deposit.get('body'))
        deposit = int( (sumOfDeposit("principle") + sumOfDeposit("interest_earned")) )

    fund = int(sumOfFund("balance_units_value"))
     
    worth = fund+deposit+pf_amount
    body = list()

    for x in listOfInstruments:
        if x == 'Mutual Funds':
            tmp_dct = {
            "amount": fund,
            "type": x,
            "add_new_url" : "/website/add-fund",
            "details_url" : "/website/fund-list",
            "button_text" : "Add New"
        }
        if x == 'Deposits':
            tmp_dct = {
            "amount": deposit,
            "type": x,
            "add_new_url" : "/website/add-deposit",
            "details_url" : "/website/deposit-list",
            "button_text" : "Add New"
        }
        if x == 'Provident Fund':
            tmp_dct = {
            "amount": pf_amount,
            "type": x,
            "add_new_url" : "#",
            "details_url" : "#",
            "button_text" : ""
        }
        if x == 'Gold':
            tmp_dct = {
            "amount": "0.0",
            "type": x,
            "add_new_url" : "#",
            "details_url" : "#",
            "button_text" : "Add New"
        }

        body.append(tmp_dct)

    return templates.TemplateResponse(
        "home.html", 
        {
            "request": request,
            "worth":worth,
            "listOfInstruments" : body
        }
    )