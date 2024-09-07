
import decimal
import json
from boto3.dynamodb.conditions import Key
import json, boto3
import pendulum


dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('account_and_user_profile')
table2 = dynamodb.Table('deposits')

def deposit_details(user_details):
    # Get the default context
    context = decimal.getcontext()
    
    # Change the context to allow inexact and rounded results
    context.traps[decimal.Inexact] = False
    context.traps[decimal.Rounded] = False

    response = list()

    try:
        values = table2.query(  KeyConditionExpression = Key('account_id').eq(decimal.Decimal(user_details['account_id'])) )
        
        if values['Items']:
            for value in values['Items']:
                if user_details['profile']!=value['profile']:
                    continue
                depositType = value['type']
                principle = float(value['principle'])
                rate = float(value['rate'])
                freq = float(value['frequency'])
                start = pendulum.parse(value['start_date'], strict=False).date() 
                maturity = pendulum.parse(value['maturity_date'], strict=False).date() 
                
                date2 = pendulum.today().date() if maturity >= pendulum.today().date() else maturity

                if depositType == 'FD':

                    if True:
                        rate = rate/366
                        interest = 0
                        while start <= date2:
                            interest = interest +(  principle * rate/100 )

                            if start.day == 31 and start.month == 3:
                                principle+=interest
                                interest=0
                            elif start.day == 30 and start.month == 6:
                                principle+=interest
                                interest=0
                            elif start.day == 30 and start.month == 9:
                                principle+=interest
                                interest=0
                            elif start.day == 31 and start.month == 12:
                                principle+=interest
                                interest=0

                            start = start.add(days=1)

                        if interest != 0:
                            principle+=interest 

                        amount = principle

                    response.append(amount) 

                if depositType=='RD':
                    rd_current_interest = 0
                    show_c_time = c_time = (pendulum.today().date()-start).in_months() + 1 # this +1 is because we have already paid the first installment before the fist month completed

                    while c_time>=1:
                        rd_current_interest += principle*( ( 1 + ( (rate/freq)/100) )**( freq*c_time/12 ) ) - principle
                        c_time -=1
                    
                    response.append( (principle*show_c_time)+rd_current_interest )

        jsonData =  table.query(  KeyConditionExpression = Key('account_id').eq(decimal.Decimal(user_details['account_id'])) & Key('profile').eq(user_details['profile']) )

        jsonData = jsonData.get('Items')[0]
        
        totalAmount = round(sum(response))
        
        print(response)

        jsonData['current_deposit_amount'] = decimal.Decimal(str(totalAmount))

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
        reponse = deposit_details(user_details)
        print(reponse)
