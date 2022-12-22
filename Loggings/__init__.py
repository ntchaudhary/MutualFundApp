import logging
import os
import configparser


def getLogger(name):
    parser = configparser.ConfigParser()
    tmp = 'D:/Users/tushar/Documents/Projects/mutualFundAPI/'

    parser.read(os.path.join(tmp, "Loggings\\log.cfg"))
    formatter = logging.Formatter(parser.get(section='Formatter', option='format', raw=True))

    filePath = tmp + parser.get(section='file', option='filePath')

    fileHandler = logging.FileHandler(filename=filePath)
    fileHandler.setFormatter(formatter)

    logger = logging.getLogger(name)

    logger.setLevel(parser['logMode']['level'])
    logger.addHandler(fileHandler)

    return logger
