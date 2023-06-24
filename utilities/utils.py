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