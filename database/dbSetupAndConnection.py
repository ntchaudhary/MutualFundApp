import json
import sqlite3


class Connection:
    def __init__(self):
        self.conn = sqlite3.connect("database/counter.db")

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


def createTableOnFundCode(code, dbObj):
    strObj = f''' CREATE TABLE FUND_{code}
                 (
                    UNITS_DATE           DATE,
                    NUMBER_OF_UNITS      DECIMAL(10,5),
                    AMOUNT_INVESTED      DECIMAL(10,5),
                    TAX_HARVESTED        TEXT DEFAULT 'NO'                   
                 );
                 '''
    cur = dbObj.conn.cursor()
    cur.execute(strObj)


if __name__ == '__main__':
    setup = Connection()
    with open('../static/Data.json', 'rb') as dataFile:
        CONSTANTS = json.load(dataFile)
    SCHEME_CODE = list(CONSTANTS.keys())
    [createTableOnFundCode(x, setup) for x in SCHEME_CODE]
    setup.conn.close()
    del setup
