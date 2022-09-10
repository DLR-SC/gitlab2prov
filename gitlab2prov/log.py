import logging


LEVEL = logging.DEBUG
FORMAT = "[%(asctime)s] %(levelname)s :: %(filename)s :: %(funcName)s :: %(message)s"


def create_logger():
    logging.basicConfig(
        level=LEVEL,
        format=FORMAT,
        filename="gitlab2prov.log",
        filemode="a",
    )
