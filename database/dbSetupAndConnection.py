import json, boto3, sqlite3
from decimal import Decimal


class Connection:
    def __init__(self):
        self.conn = sqlite3.connect("database/counter.db")
        self.dynamodb = boto3.resource('dynamodb') 

    def insertFileData(self, code, file=(None, None, None)):
        sqlstmt = f''' INSERT INTO FUND_{code} (UNITS_DATE, NUMBER_OF_UNITS, AMOUNT_INVESTED) VALUES(?, ?, ?)'''
        cur = self.conn.cursor()
        cur.execute(sqlstmt, file)
        self.conn.commit()

    def deleteRows(self, code, date):
        sqlstmt = f''' DELETE FROM FUND_{code} WHERE UNITS_DATE = ?'''
        cur = self.conn.cursor()
        cur.execute(sqlstmt, (date,))
        self.conn.commit()

    def updateRows(self, code, date):
        sqlstmt = f''' UPDATE FUND_{code} SET TAX_HARVESTED='YES' WHERE UNITS_DATE = ?'''
        cur = self.conn.cursor()
        cur.execute(sqlstmt, (date,))
        self.conn.commit()

    def insertDynamodbRow(self, tableName, insertData: list, convert=False):
        table = self.dynamodb.Table(tableName)
        for insert_json in insertData:
            if convert:
                insert_json = json.loads(json.dumps(insert_json), parse_float=Decimal, parse_int=Decimal)
            response = table.put_item(Item=insert_json)

    def updateDynamodbRow(self,tableName, key, update_expression, expression_attribute_values, expression_attribute_name):
        table = self.dynamodb.Table(tableName)
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_name
        )

    def deleteDynamodbRow(self, tableName, key):
        table = self.dynamodb.Table(tableName)
        response = table.delete_item( Key = key )

    def createFundTable(self, code):
        strObj = f''' CREATE TABLE FUND_{code}
                     (
                        UNITS_DATE           DATE,
                        NUMBER_OF_UNITS      DECIMAL(10,5),
                        AMOUNT_INVESTED      DECIMAL(10,5),
                        TAX_HARVESTED        TEXT DEFAULT 'NO'                   
                     );
                     '''
        cur = self.conn.cursor()
        cur.execute(strObj)



def createDepositTables(dbObj):

    # strObj = f''' drop table DEPOSIT '''
    strObj = f''' CREATE TABLE DEPOSIT
                 (
                    ID                  SERIAL      PRIMARY KEY,
                    NAME                TEXT,
                    TYPE                TEXT,
                    PRINCIPLE           DECIMAL(10,5),
                    RATE                DECIMAL(10,5),
                    FREQ                DECIMAL(1),
                    MATURITY_DATE       DATE,
                    START_DATE          DATE                
                 );
                 '''
    cur = dbObj.conn.cursor()
    cur.execute(strObj)


if __name__ == '__main__':
    setup = Connection()
    # with open('../static/Data.json', 'rb') as dataFile:
    #     CONSTANTS = json.load(dataFile)
    # SCHEME_CODE = list(CONSTANTS.keys())
    # [createTableOnFundCode(x, setup) for x in SCHEME_CODE]
    createDepositTables(setup)
    setup.conn.close()
    del setup
