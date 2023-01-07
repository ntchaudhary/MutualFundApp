from decimal import Decimal
import pandas as pd
import pendulum
from database.dbSetupAndConnection import Connection
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter

depositeDetails = APIRouter()

@depositeDetails.get('/details')
def _handler() -> dict:
    """Return list of all the investment made in fixed and Recurring desposits and the amount they have made till today"""
    
    _DB = Connection()
    response = list()
    existsCheck = f''' select ID, NAME, TYPE, PRINCIPLE, RATE, FREQ, START_DATE, MATURITY_DATE from DEPOSIT '''
    

    try:
        cur = _DB.conn.cursor() 
        
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

                    dct_resp = {
                        "id" : id,
                        "name":name,
                        "type": "Fixed Deposit",
                        "principle":principle,
                        "rate":rate,
                        "duration":f"{(maturity-start).in_months()} months",
                        "start_date": start,
                        "maturity_date":maturity,
                        "maturity_amount": round(amount,0),
                        "interest_earned": round(c_interest,2),
                    }   
                    response.append(dct_resp)

                if depositType=='RD':

                    show_time = time = (maturity-start).in_months()
                    c_time = (pendulum.today().date()-start).in_months()

                    rd_amount=0
                    rd_current_interest = 0

                    while time>=1:
                        rd_amount += principle*( ( 1 + ( (rate/freq)/100) )**( freq*time/12 ) )
                        time -=1

                    while c_time>=1:
                        rd_current_interest += principle*( ( 1 + ( (rate/freq)/100) )**( freq*c_time/12 ) ) - principle
                        c_time -=1

                    dct_resp = {
                        "id" : id,
                        "name":name,
                        "type": "Recurring Deposit",
                        "principle":principle*show_time,
                        "rate":rate,
                        "duration":f"{show_time} months",
                        "start_date": start,
                        "maturity_date":maturity,
                        "maturity_amount": round(rd_amount , 0),
                        "interest_earned": round(rd_current_interest, 2),
                    }   
                    response.append(dct_resp)
        else:
            raise ValueError(f'No Deposite is present in system')

    except ValueError as e:
        response = {
            "ERROR": "404",
            "message": str(e)
        }
    except Exception as e:
        response = {
            "ERROR": "500",
            "message": str(e)
        }


    return(response)