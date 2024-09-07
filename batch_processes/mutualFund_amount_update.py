from decimal import Decimal
import json
from boto3.dynamodb.conditions import Key
import json, boto3
import pandas as pd

dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('account_and_user_profile')
table2 = dynamodb.Table('fund_details')
table3 = dynamodb.Table('fund_transactions_details')

def mutual_fund_fund_details(user_details) -> dict:
    """Return current value of all the invested funds along with gain and loss on per fund basis"""
    # _DB_OBJ = Connection()
    response = list()

    jsonData =  table.query(  KeyConditionExpression = Key('account_id').eq(Decimal(user_details['account_id'])) & Key('profile').eq(user_details['profile']) )

    jsonData = jsonData.get('Items')[0]

    SCHEME_CODE = jsonData.get('fund_owned', [])

    if not SCHEME_CODE:
        return {
            "message": 'No mutual funds found'
        } 

    try:
        for schemeCode in SCHEME_CODE:

            db_data_all = table3.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items']
            currentMarketPrice = table2.query(KeyConditionExpression = Key('fund_id').eq(f"{schemeCode}") )['Items'][0]
            db_data = [x for x in db_data_all if str(x["account_id"])==str(jsonData["account_id"]) and str(x["profile"])==str(jsonData["profile"])]
            if not db_data:
                db_data.append({'AMOUNT_INVESTED': Decimal('0.0'),
                'NUMBER_OF_UNITS': Decimal('0.0'),
                'UNITS_DATE': '31-01-2022'})
            dataframe = pd.DataFrame(db_data)
            
            currentMarketPrice['scheme_code'] = currentMarketPrice['fund_id']
            del currentMarketPrice['fund_id']

            market_value = round(float(dataframe.NUMBER_OF_UNITS.sum())*float(currentMarketPrice['nav'])) # current market value of all units
            

            response.append(market_value)

        jsonData['current_fund_amount'] = Decimal(sum(response))
        # x = json.loads(json.dumps(jsonData), parse_float=Decimal, parse_int=Decimal)
        response = table.put_item(Item=jsonData)
        response = {
            "message": 'success'
        } 

    except Exception as e:
        response = {
            "message": str(e)
        }

    return(response)



def lambda_handler(event, context):
    # TODO implement
    user_details = {
        "account_id": None,
        "profile": None
    }

    for message in event.get('Records'):
        body = json.loads(message.get('body'))
        user_details['account_id'] = body.get('account')
        user_details['profile'] = body.get('profile')

        print(f'going for user : {user_details}')
        reponse = mutual_fund_fund_details(user_details)
        print(reponse)
        
