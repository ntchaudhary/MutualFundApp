from datetime import datetime
from mftool import Mftool
from boto3.dynamodb.conditions import Key
import json, boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests

DEPOSIT_SQS_URL = 'https://sqs.ap-south-1.amazonaws.com/701647385258/deposit_amount_update_queue'
MUTUAL_FUND_SQS_URL = 'https://sqs.ap-south-1.amazonaws.com/701647385258/mutualFund_amount_update_queue'

_MF = Mftool()

def lambda_handler(event, context):
    """this lambda function executes daily (tuesday to saturday) at 5 am to update the nav of the fund available in system"""
    dynamodb = boto3.resource('dynamodb')
    table1 = dynamodb.Table('fund_details') # type: ignore

    response = table1.scan()

    items = list()

    items = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table1.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    fund_data = dict()

    for data in items:

        if 'mf' in data['fund_id']:
            x = _MF.get_scheme_quote(data['fund_id'].split('__')[1])
            x['fund_id'] = data['fund_id']
            x['exitTime'] = int(data.get('exitTime', 9))
            del x['scheme_code']

        if 'nps' in data['fund_id']:
            nps = {}
            nps = json.loads(requests.get(f"https://npsnav.in/api/detailed/{data['fund_id'].split('__')[1]}")) # type: ignore
            x = {
            "fund_id": data['fund_id'],
            "exitTime": 99,
            "last_updated": nps['Last Updated'],
            "nav": str(nps['NAV']),
            "scheme_name": nps['Scheme Name']
            }

        x = json.loads(json.dumps(x))
        response = table1.put_item(Item=x)
        fund_data[x['fund_id']] = x['nav']
            
    print("Successfully Updated")

    try:

        table2 = dynamodb.Table('account_and_user_profile') # type: ignore
        response_table2 = table2.scan()

        items_table2 = response_table2['Items']

        while 'LastEvaluatedKey' in response_table2:
            response_table2 = table2.scan(ExclusiveStartKey=response_table2['LastEvaluatedKey'])
            items_table2.extend(response_table2['Items'])

        # Create a new SQS client
        sqs =  boto3.client('sqs')

        for data in items_table2:
            if data.get("profile_status") != 'active':
                continue

            messageAtributes = {
                "account_id": str(data.get("account_id")),
                "profile": str(data.get("profile")),
                "operation": "nav",
                "fund_data":fund_data
                }
                
            messageBody = json.dumps(messageAtributes)

            # Send the message
            if data.get('fund_owned') != 'no':
                response_mutual_fund = sqs.send_message(
                                        QueueUrl=MUTUAL_FUND_SQS_URL,
                                        MessageBody=messageBody,
                                        # MessageGroupId='batch'
                )
                print(f'Mutual Fund Message ID: {response_mutual_fund["MessageId"]}')

            if datetime.now().day == 1:                        
                response_deposit = sqs.send_message(
                                        QueueUrl=DEPOSIT_SQS_URL,
                                        MessageBody=messageBody,
                                        # MessageGroupId='batch'
                                    )
            # Print out the response
                print(f'Deposit Message ID: {response_deposit["MessageId"]}')
            
    except NoCredentialsError:
        print("Error: No AWS credentials found.")
    except PartialCredentialsError:
        print("Error: Incomplete AWS credentials found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return "Successfully Updated"


# lambda_handler(None, None)