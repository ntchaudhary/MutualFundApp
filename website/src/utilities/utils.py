
def calculateSumFromListOFDict(listOfDictry):
    return lambda key: sum([float(y.get(key)) for y in listOfDictry])
