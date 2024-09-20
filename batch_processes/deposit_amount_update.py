
import asyncio
import decimal
import json
from boto3.dynamodb.conditions import Key
import json, boto3
import pendulum


dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('account_and_user_profile')
table2 = dynamodb.Table('deposits')

async def deposit_details(user_details):
    # Get the default context
    context = decimal.getcontext()
    
    # Change the context to allow inexact and rounded results
    context.traps[decimal.Inexact] = False
    context.traps[decimal.Rounded] = False

    response = list()

    try:
        await asyncio.sleep(0.000001)
        values = table2.query(  KeyConditionExpression = Key('account_id').eq(decimal.Decimal(user_details['account_id'])) )
        await asyncio.sleep(0.000001)

        if values['Items']:
            for value in values['Items']:

                accrued_interest = 0
                
                depositType = value['type']
                principle = float(value['principle'])
                installment = float(value['installment'])
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

                    accrued_interest = amount - float(value['principle'])

                    try:
                        await asyncio.sleep(0.000001)
                        response_interest = table2.update_item (
                            Key = {'account_id': decimal.Decimal(value['account_id']), 'id': decimal.Decimal(value['id'])},
                            UpdateExpression='SET interest_earned = :interest_earned',           
                            ExpressionAttributeValues={
                                ':interest_earned': decimal.Decimal(str(round(accrued_interest,2)))
                            },
                            ReturnValues='UPDATED_NEW'
                        )
                        await asyncio.sleep(0.000001)
                    except Exception as err:
                        print('Error updating FD item',err)

                if depositType=='RD':
                    rd_current_interest = 0
                    show_c_time = c_time = (pendulum.today().date()-start).in_months() + 1 # this +1 is because we have already paid the first installment before the fist month completed

                    while c_time>=1:
                        rd_current_interest += installment*( ( 1 + ( (rate/freq)/100) )**( freq*c_time/12 ) ) - installment
                        c_time -=1
                    
                    response.append( (installment*show_c_time)+rd_current_interest )
                    accrued_interest = rd_current_interest

                    try:
                        await asyncio.sleep(0.000001)
                        response_interest = table2.update_item (
                            Key = {'account_id': decimal.Decimal(value['account_id']), 'id': decimal.Decimal(value['id'])},
                            UpdateExpression='SET interest_earned = :interest_earned, principle = :principle',           
                            ExpressionAttributeValues={
                                ':interest_earned': decimal.Decimal(str(round(accrued_interest,2))),
                                ':principle': decimal.Decimal(str(installment*show_c_time))
                            },
                            ReturnValues='UPDATED_NEW'
                        )
                        await asyncio.sleep(0.000001)
                    except Exception as err:
                        print('Error updating RD item',err)

                print('deposite table update',response_interest['Attributes'])
        
        totalAmount = round(sum(response))
        
        print(response)        
    
        response = table.update_item (
            Key={'account_id': decimal.Decimal(user_details['account_id']), 'profile': user_details['profile']},    # Specify the primary key
            UpdateExpression='SET current_deposit_amount = :current_deposit_amount',                                # Update expression
            ExpressionAttributeValues={
                ':current_deposit_amount': decimal.Decimal(str(totalAmount))                                        # New value for the email attribute
            },
            ReturnValues='UPDATED_NEW'                                                                              # Returns the updated attributes
        )

        print('Account and user table update', response['Attributes'])

        return{'message : successfully updated '}

    except Exception as e:
        output= {
            "message": str(e)
        }
        print(output)
        return(output)


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
        try:
            reponse = asyncio.run(deposit_details(user_details))
        except Exception as err:
            response = f"error occured { err}"
        print(reponse)
    return None
    