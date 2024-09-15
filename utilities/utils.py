from decimal import Decimal
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import json, boto3

def calculateSumFromListOFDict(listOfDictry):
    return lambda key: sum([float(y.get(key)) for y in listOfDictry])


def convertResponse(data: dict):
    newResponse = dict()
    for key, values in data.items():
        newResponse[key] = str(values)
    return newResponse


class MyObject:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


def convertDecimalAndGroupByYear(data: list) -> dict :

    segregated_data = {}

    for dic in data:

        value = dic.get('expense_date')[0:4]
        if value not in segregated_data:
            segregated_data[value] = []

        tempDict = dict()
        
        # changing the data type to either float or string
        for keys, values in dic.items():
            if isinstance(values, Decimal):
                tempDict[keys] = float(values)
            else:
                tempDict[keys] = str(values)

        segregated_data[value].append(tempDict)
    
    return segregated_data


def convertDecimal(data: list) -> list :

    segregated_data = list()

    for dic in data:

        tempDict = dict()
        
        # changing the data type to either float or string
        for keys, values in dic.items():
            if isinstance(values, Decimal):
                tempDict[keys] = float(values)
            else:
                tempDict[keys] = values

        segregated_data.append(tempDict)
    
    return segregated_data


def sendMessageToQueue(messageAtributes:dict, queue_url_deposit):

    try:
        # Create a new SQS client
        sqs = boto3.client('sqs')
                
        messageBody = json.dumps(messageAtributes)

        # Send the message
        response = sqs.send_message(
                                        QueueUrl=queue_url_deposit,
                                        MessageBody=messageBody,
                                        # MessageGroupId='batch'
                                    )
        # Print out the response
        print(f'Message ID: {response["MessageId"]}')
            
    except NoCredentialsError:
        raise Exception ("Error: No AWS credentials found.")
    except PartialCredentialsError:
        raise Exception ("Error: Incomplete AWS credentials found.")
    except Exception as e:
        raise Exception (f"An error occurred: {e}")
