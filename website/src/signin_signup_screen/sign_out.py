from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse



signOUT = APIRouter()
templates = Jinja2Templates(directory="website/UI")

@signOUT.get('/sign-out')
def signout_post(request: Request):

    response = RedirectResponse(url="/sign-in", status_code=303)
    response.delete_cookie(key="token")
    return response