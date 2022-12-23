def formatResponse(statusCode, header, response):
    return {"status_code": statusCode, "allowed_header": header, "body": response}


def convertResponse(data: dict):
    newResponse = dict()
    for key, values in data.items():
        newResponse[key] = str(values)
    return newResponse


def calculateSumFromListOFDict(listOfDictry):
    return lambda key: sum([float(y.get(key)) for y in listOfDictry])
