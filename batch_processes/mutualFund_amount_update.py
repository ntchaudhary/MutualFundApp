from decimal import Decimal
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import json, boto3
import pandas as pd

dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('account_and_user_profile')
table2 = dynamodb.Table('fund_details')
table3 = dynamodb.Table('fund_owned_details')
table4 = dynamodb.Table('fund_transaction_details')

def update_fund_details(fund_detail):
    from mftool import Mftool

    _MF = Mftool()

    try:

        x = _MF.get_scheme_quote(fund_detail['fund_id']) 

        response_fund_owned = table3.update_item(
            Key = {
                'account_id': str(fund_detail['account_id']),
                'fund_id': str(fund_detail['fund_id'])
            },
            UpdateExpression='SET nav = :nav, exit_time = :exit_time',
            ExpressionAttributeValues={
                ':nav': x.get('nav', 0),
                ':exit_time': 9
            },
            ReturnValues='UPDATED_NEW'
        )

        print('fund owned update', response_fund_owned['Attributes'])

        x['fund_id'] = x['scheme_code']
        del x['scheme_code']
        x['exitTime'] = 9
        x = json.loads(json.dumps(x))

        table2.put_item(Item=x,ConditionExpression = 'attribute_not_exists(fund_id)')

        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("Item with the same partition key and sort key already exists.")
        else:
            print("Unexpected client error occurred:", e)
        
    except Exception as e:
        print("Unexpected error occurred:", e)


def update_invested_details(fund_detail):
    try:

        fund_transactions = table4.query(
            KeyConditionExpression = Key('account_id').eq(str(fund_detail['account_id']),) & Key('fund_id__id').begins_with(str(fund_detail['fund_id'])) 
        )['Items']
        
        total_units = 0
        invested = 0

        for row in fund_transactions:
            total_units += float(row['number_of_units'])
            invested += float(row['amount_invested'])
        
        response_fund_owned = table3.update_item(
            Key = {
                'account_id': str(fund_detail['account_id']),
                'fund_id': str(fund_detail['fund_id'])
            },
            UpdateExpression='SET invested = :invested, total_units = :total_units',
            ExpressionAttributeValues={
                ':invested': str(invested),
                ':total_units': str(total_units)
            },
            ReturnValues='UPDATED_NEW'
        )

        print('fund owned updated from update_invested_details function', response_fund_owned['Attributes'])
        
    except Exception as e:
        print("Unexpected error occurred:", e)

    update_account_and_user_profile(fund_detail)


def update_account_and_user_profile(user_details):
    all_fund_transactions = table3.query(
            KeyConditionExpression = Key('account_id').eq(str(user_details['account_id'])) 
        )['Items']
    
    total_amount = 0
    for row in all_fund_transactions:
        total_amount += float(row['total_units']) * float(row['nav'])

    response = table.update_item (
        Key={'account_id': Decimal(user_details['account_id']), 'profile': user_details['profile']},
        UpdateExpression='SET current_fund_amount = :current_fund_amount',           
        ExpressionAttributeValues={
            ':current_fund_amount': str(round(total_amount))
        },
        ReturnValues='UPDATED_NEW'
    )

    print('Account and user table update', response['Attributes'])


def lambda_handler(event, context):
    # TODO implement
    fund_detail = dict()
    for message in event.get('Records'):
        body = json.loads(message.get('body'))
        fund_detail['account_id'] = body.get('account_id')
        fund_detail['fund_id'] = body.get('fund_id')
        fund_detail['profile'] = body.get('profile')

        operation = body.get('operation')

        print(f'going for user : {fund_detail}, {operation}')
        
        if operation == 'new':
            update_fund_details(fund_detail)
        elif operation == 'buy':
            update_invested_details(fund_detail)

        