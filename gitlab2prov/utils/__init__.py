import argparse
import datetime
import urllib.parse
import uuid
from typing import Any, Iterator, List

from prov.model import ProvDocument


def group_by(ungrouped, group_size_index):
    start = 0
    grouped = []
    for group_size in group_size_index:
        group = ungrouped[start:(start + group_size)]
        flattened = [member for members in group for member in members]
        grouped.append(flattened)
        start += group_size
    return grouped

def p_time(string: str) -> datetime.datetime:
    """
    Parse datetime string to datetime object.
    """
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: expected type str, got type {type(string)}.")

    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    return datetime.datetime.strptime(string, fmt)

def url_encoded_path(url: str) -> str:
    """
    Extract project path from url and replace "/" by "%2F".
    """
    if not isinstance(url, str):
        raise TypeError(f"Parameter url: Expected type str, got type {type(url)}.")

    path = urllib.parse.urlparse(url).path

    if not path:
        raise ValueError(f"Could not parse path from {url}.")

    if path.endswith("/"):
        path = path[:-1]

    if not path:
        raise ValueError(f"Empty path parsed from {url}.")

    return path[1:].replace("/", "%2F")


def q_name(string: str) -> str:
    """
    Return string representation of uuid5 of *string*.

    Creates unique identifiers.
    """
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: Expected type str, got type {type(string)}.")

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, string))
