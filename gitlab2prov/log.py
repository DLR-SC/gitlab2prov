import logging
import sys


LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(funcName)s %(message)s"


def create_logger(dest=None):
    logging.basicConfig(
        stream=sys.stdout,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
    )
    if dest is not None:
        root = logging.getLogger("")
        fileHandler = logging.FileHandler(dest)
        root.addHandler(fileHandler)
