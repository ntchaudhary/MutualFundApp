
from mftool import Mftool
from mutualFundApp.src.utilities.utils import *

from fastapi import APIRouter

availableFundList = APIRouter()
header = "localhost"


@availableFundList.put('/available-fund-list')
def _handler() -> dict:
    try:
        _MF = Mftool()

        all_scheme_codes = _MF.get_scheme_codes(as_json=True)

        fileObj = open('mutualFundApp\\src\\static\\fundList.json', 'w')

        fileObj.write(all_scheme_codes)

        fileObj.close()

        statusCode = 200
        response = "LIST UPDATED SUCCESSFULLY"
    except Exception as e:
        statusCode = 500
        response = {
            "ERROR": e.args[0]
        }

    return formatResponse(statusCode, header, response)
