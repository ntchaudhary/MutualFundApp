import json, boto3, sqlite3
from decimal import Decimal


class Connection:
    def __init__(self):

        self.dynamodb = boto3.resource('dynamodb') 

    def insertDynamodbRow(self, tableName, insertData: list, convert=False):
        table = self.dynamodb.Table(tableName) # type: ignore
        for insert_json in insertData:
            if convert:
                insert_json = json.loads(json.dumps(insert_json), parse_float=Decimal, parse_int=Decimal)
            response = table.put_item(Item=insert_json)

    def updateDynamodbRow(self,tableName, key, update_expression, expression_attribute_values, expression_attribute_name):
        table = self.dynamodb.Table(tableName) # type: ignore
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_name
        )

    def deleteDynamodbRow(self, tableName, key):
        table = self.dynamodb.Table(tableName) # type: ignore
        response = table.delete_item( Key = key )
