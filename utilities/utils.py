from decimal import Decimal

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
