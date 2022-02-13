import uuid
import random


def random_suffix():
    return uuid.uuid4().hex[:6]
