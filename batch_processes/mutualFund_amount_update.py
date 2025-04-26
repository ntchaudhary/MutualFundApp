from decimal import Decimal
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
import json, boto3
import requests

dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('account_and_user_profile')
table2 = dynamodb.Table('fund_details')
table3 = dynamodb.Table('fund_owned_details')
table4 = dynamodb.Table('fund_transaction_details')

def update_fund_details(fund_detail):
    from mftool import Mftool

    _MF = Mftool()
    x=dict()

    try:
        if 'mf' in fund_detail['fund_id']:
            x = _MF.get_scheme_quote(fund_detail['fund_id'].split('__')[1])
            del x['scheme_code']

        if 'nps' in fund_detail['fund_id']:
            nps = {}
            nps = json.loads(requests.get(f"https://npsnav.in/api/{fund_detail['fund_id'].split('__')[1]}"))
            x = {
            "fund_id": fund_detail['fund_id'],
            "exitTime": 99,
            "last_updated": nps['Last Updated'],
            "nav": nps['NAV'],
            "scheme_name": nps['Scheme Name']
            }

        response_fund_owned = table3.update_item(
            Key = {
                'account_id': str(fund_detail['account_id']),
                'fund_id': str(fund_detail['fund_id'])
            },
            UpdateExpression='SET nav = :nav, exit_time = :exit_time, reinvest_units = :reinvest_units, reinvest_units_amount = :reinvest_units_amount, invested = :invested, total_units = :total_units',
            ExpressionAttributeValues={
                ':nav': x.get('nav', 0),
                ':exit_time': 99, 
                ':reinvest_units' : 0, 
                ':reinvest_units_amount' : 0, 
                ':invested' : 0, 
                ':total_units'  :0
            },
            ReturnValues='UPDATED_NEW'
        )

        print('fund owned update', response_fund_owned['Attributes'])

        x['fund_id'] = fund_detail['fund_id']
        x['exitTime'] = 99
        x = json.loads(json.dumps(x))

        table2.put_item(Item=x,ConditionExpression = 'attribute_not_exists(fund_id)')

        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("Item with the same partition key and sort key already exists.")
        else:
            print("Unexpected client error occurred:", e)
        
    except Exception as e:
        print("Unexpected error occurred:", e)

def update_invested_details(fund_detail, operation):
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

    if operation == 'sell':
        update_reinvest_units(fund_detail)

    update_account_and_user_profile(fund_detail)

def update_reinvest_units(fund_detail):

    exitTime = table2.query(KeyConditionExpression = Key('fund_id').eq(f"{fund_detail['fund_id']}") )['Items']

    # Calculate the date one year ago from today
    one_year_ago = datetime.now() - timedelta(days=365*float(exitTime[0].get('exitTime', 9 )))

    try:
        response = table4.query(
            KeyConditionExpression = Key('account_id').eq(str(fund_detail['account_id']),) & Key('fund_id__id').begins_with(str(fund_detail['fund_id'])) ,
            ScanIndexForward=True
        )['Items']

        units = 0
        amount = 0

        breakLoop = 0

        for row in response:

            unit_date_str = row['unit_date']
            unit_date = datetime.strptime(unit_date_str, '%d-%m-%Y')
            
            if unit_date < one_year_ago:
                units+= float(row['number_of_units'])
                amount+= float(row['amount_invested'])
            else:
                breakLoop+=1

                if breakLoop > 9:
                    break


        response_fund_owned = table3.update_item(
                Key = {
                    'account_id': str(fund_detail['account_id']),
                    'fund_id': str(fund_detail['fund_id'])
                },
                UpdateExpression='SET reinvest_units = :reinvest_units, reinvest_units_amount = :reinvest_units_amount',
                ExpressionAttributeValues={
                    ':reinvest_units': str(units),
                    ':reinvest_units_amount': str(amount)
                },
                ReturnValues='UPDATED_NEW'
            )
        
        print(' line 122 fund owned updated from update_reinvest_units function', response_fund_owned['Attributes'])
        
    except Exception as e:
        print("Unexpected error occurred:", e)

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

def update_nav(fund_detail, fund_data):
    per_account_funds = table3.query(
            KeyConditionExpression=Key('account_id').eq(str(fund_detail['account_id'])),
            ProjectionExpression = 'fund_id'
        )['Items']
    
    for row in per_account_funds:
        
        response_fund_owned = table3.update_item(
                Key = {
                    'account_id': str(fund_detail['account_id']),
                    'fund_id': str(row['fund_id'])
                },
                UpdateExpression='SET nav = :nav',
                ExpressionAttributeValues={
                    ':nav': fund_data.get(row['fund_id'],0)
                },
                ReturnValues='UPDATED_NEW'
            )
        
        if datetime.now().day == 1:
            fund_detail['fund_id'] = row['fund_id']
            update_reinvest_units(fund_detail)
        
        print('fund owned updated from update_nav function', response_fund_owned['Attributes'])

    update_account_and_user_profile(fund_detail)


def lambda_handler(event, context):
    # TODO implement
    fund_detail = dict()
    for message in event.get('Records'):
        body = json.loads(message.get('body'))
        print('body received',body)
        fund_detail['account_id'] = body.get('account_id')
        fund_detail['fund_id'] = body.get('fund_id')
        fund_detail['profile'] = body.get('profile')

        operation = body.get('operation')

        print(f'going for user : {fund_detail}, {operation}')
        
        try:
        
            if operation == 'new':
                update_fund_details(fund_detail)
            elif operation == 'buy':
                update_invested_details(fund_detail, operation)
            elif operation == 'sell':
                update_invested_details(fund_detail, operation)
            elif operation == 'nav':
                update_nav(fund_detail, body.get('fund_data'))
        except Exception as err:
            print("error occured ", err)
            
    
    return None

