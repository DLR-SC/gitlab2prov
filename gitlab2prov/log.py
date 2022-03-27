import logging


LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(funcName)s %(message)s"


def create_logger(dest=logging.StreamHandler()):
    logging.basicConfig(
        filename=dest,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
    )
