from mftool import Mftool
from fastapi import APIRouter

availableFundList = APIRouter()


@availableFundList.put('/available-fund-list')
def _handler() -> dict:
    try:
        _MF = Mftool()

        all_scheme_codes = _MF.get_scheme_codes(as_json=True)

        fileObj = open('static/mutualFundApp/fundList.json', 'w')

        fileObj.write(all_scheme_codes)

        fileObj.close()
        response = "LIST UPDATED SUCCESSFULLY"
    except Exception as e:
        
        response = {
            "ERROR": e.args[0]
        }

    return (response)
