import json

import pendulum

CURRENT_YEAR = pendulum.today().year

CURRENT_MONTH = pendulum.today().month

SIP_DATE = 25

STAMP_DUTY_PERCENT = 0.005

with open('mutualFundApp\src\static\Data.json', 'rb') as dataFile:
    CONSTANTS = json.load(dataFile)
SCHEME_CODE = list(CONSTANTS.keys())
