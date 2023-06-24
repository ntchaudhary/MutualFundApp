
from database.dbSetupAndConnection import Connection

from fastapi import APIRouter
from pydantic import BaseModel

import pendulum

CURRENT_YEAR = pendulum.today().year
CURRENT_MONTH = pendulum.today().month
CURRENT_DATE = pendulum.today().day

deposit = APIRouter()

class Body(BaseModel):
    name: str
    type: str
    principle: float
    rate: float
    compound_frequency: int
    start_date = {
        'day': CURRENT_DATE,
        'month': CURRENT_MONTH,
        'year': CURRENT_YEAR
    }
    maturity_date = {
        'day': CURRENT_DATE,
        'month': CURRENT_MONTH,
        'year': CURRENT_YEAR
    }

@deposit.post('/add')
def _add(body: Body):
    """ Add the new FD or RD entry into database"""
    _DB = Connection()
    response = list()
    name = '_'.join((body.name).split(' '))

    start_date = pendulum.date(year=body.start_date['year'], month=body.start_date['month'], day=body.start_date['day'])
    maturity_date = pendulum.date(year=body.maturity_date['year'], month=body.maturity_date['month'], day=body.maturity_date['day'])

    sqlstmt = f'''  INSERT INTO DEPOSIT (ID, NAME, TYPE, PRINCIPLE, RATE, FREQ, MATURITY_DATE,START_DATE) 
                    VALUES( (select COALESCE(max(ID),0)+1 from DEPOSIT), '{name}','{body.type}','{body.principle}','{body.rate}','{body.compound_frequency}','{maturity_date}','{start_date}') '''
    try:
        cur = _DB.conn.cursor()
        cur.execute(sqlstmt)
        _DB.conn.commit()
        response = {
            "status" : 200,
            "message": "DEPOSIT ADDED SUCCESSFULLY"
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }
    return response


@deposit.delete('/delete/{fdID}')
def _delete(fdID: str):
    """Delete FD or RD entry from database"""
    _DB = Connection()
    response = list()
    existsCheck = f''' select * from DEPOSIT where ID = '{fdID}' '''
    sqlstmt = f''' delete from DEPOSIT where ID = '{fdID}' '''

    try:
        cur = _DB.conn.cursor() 
        
        value = cur.execute(existsCheck).fetchall()

        if value: 
            cur.execute(sqlstmt)
            _DB.conn.commit()
        else:
            raise ValueError(f'FD with ID as {fdID} does not exists')

        response = {
            "status" : 200,
            "message": "DEPOSIT DELETED SUCCESSFULLY"
        }
    except ValueError as e:
        response = {
            "status": 404,
            "message": str(e)
        }
    except Exception as e:
        response = {
            "status": 500,
            "message": str(e)
        }

    return(response)
        