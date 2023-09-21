from mftool import Mftool
from boto3.dynamodb.conditions import Key
import json, boto3

_MF = Mftool()

def lambda_handler(event, context):
    """this lambda function executes daily (tuesday to saturday) at 5 am to update the nav of the fund available in system"""
    dynamodb = boto3.resource('dynamodb')
    table1 = dynamodb.Table('account_and_user_profile')
    table2 = dynamodb.Table('fund_details')

    response = table1.scan()

    items = list()

    items = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table1.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    fundIDs = []

    for data in items:
         for id in data.get('fund_owned',[]):
            fundIDs.append(id)

    for id in list(set(fundIDs)):
        currentEntry = table2.query(KeyConditionExpression = Key('fund_id').eq(f"{id}") )['Items'][0]
        x = _MF.get_scheme_quote(id)
        x['fund_id'] = x['scheme_code']
        x['exitTime'] = currentEntry.get('exitTime', 9999)
        del x['scheme_code']
        x = json.loads(json.dumps(x))
        response = table2.put_item(Item=x)
            
    print("Successfully Updated")
    return "Successfully Updated"