from datetime import datetime
from mftool import Mftool
from boto3.dynamodb.conditions import Key
import json, boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from static.depositeApp.constants import DEPOSIT_SQS_URL
from static.mutualFundApp.constants import MUTUAL_FUND_SQS_URL


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
        x['exitTime'] = int(currentEntry.get('exitTime', 9))
        del x['scheme_code']
        x = json.loads(json.dumps(x))
        response = table2.put_item(Item=x)
            
    print("Successfully Updated")

    
    try:
        # Create a new SQS client
        sqs = boto3.client('sqs')

        for data in items:
            if data.get("profile_status") != 'active':
                continue

            messageAtributes = {
                "account": str(data.get("account_id")),
                "profile": str(data.get("profile"))
                }
                
            messageBody = json.dumps(messageAtributes)

            # Send the message
            if data.get('fund_owned',[]):
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