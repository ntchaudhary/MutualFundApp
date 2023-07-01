from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pendulum

from database.dbSetupAndConnection import Connection
from utilities.utils import MyObject
from utilities.auth import auth_wrapper

depositAdd = APIRouter()
templates = Jinja2Templates(directory="website/UI/deposit_UI")


class DepositBody(BaseModel):
    name: str
    type: str
    principle: float
    rate: float
    compound_frequency: int
    start_date: str
    maturity_date: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        principle: float = Form(...),
        gridRadios: str = Form(...),
        rate: float = Form(...),
        freqRadios: int = Form(...),
        start_date: str = Form(...),
        maturity_date: str = Form(...)
    ):
        return cls(
            name=name,
            type=gridRadios,
            principle=principle,
            rate=rate,
            compound_frequency = freqRadios,
            start_date=start_date,
            maturity_date=maturity_date
        )

def _add(body):
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


@depositAdd.get('/add-deposit', response_class=HTMLResponse)
def get_index(request: Request, user_details = Depends(auth_wrapper)):

    return templates.TemplateResponse(
        "deposit_add.html", 
        {
            "request": request,
            "show": False
        }
    )

@depositAdd.post('/add-deposit', response_class=HTMLResponse)
def post_index(request: Request, form_data: DepositBody = Depends(DepositBody.as_form), user_details = Depends(auth_wrapper)):

    start = pendulum.parse(form_data.start_date, strict=False)
    maturity = pendulum.parse(form_data.maturity_date, strict=False)

    body = {
        "name": form_data.name,
        "type": form_data.type,
        "principle": form_data.principle,
        "rate": form_data.rate,
        "compound_frequency": form_data.compound_frequency,
        "start_date": {
            'day': start.day,
            'month': start.month,
            'year': start.year
        },
        "maturity_date" : {
            'day': maturity.day,
            'month': maturity.month,
            'year': maturity.year
        }
    }

    response = _add(MyObject(**body))

    return templates.TemplateResponse(
            "deposit_add.html", 
            {
                "request": request,
                "show": True,
                "body":response
            }
        )


@depositAdd.delete('/delete/{fdID}')
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