import logging


logging.basicConfig(filename='log.log', level=logging.INFO, filemode='w')


def log(msg):
    logging.info(msg)
    print(msg)
