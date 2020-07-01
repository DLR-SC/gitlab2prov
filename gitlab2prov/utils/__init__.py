import argparse
import datetime
import urllib.parse
import uuid
from typing import Any, Iterator, List

from prov.model import ProvDocument
from provdbconnector import Neo4jAdapter, ProvDb


def store_in_db(doc: ProvDocument, config: argparse.Namespace) -> None:
    """
    Store prov document in neo4j instance.
    """
    if bundle_exists(config):
        raise KeyError(
            f"Graph for {url_encoded_path(config.project_url).replace('%2F', '-')} already exists in neo4j."
        )

    auth = {
        "user_name": config.neo4j_user,
        "user_password": config.neo4j_password,
        "host": f"{config.neo4j_host}:{config.neo4j_boltport}"
    }
    api = ProvDb(adapter=Neo4jAdapter, auth_info=auth)
    api.save_document(doc)


def p_time(string: str) -> datetime.datetime:
    """
    Parse datetime string to datetime object.
    """
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: expected type str, got type {type(string)}.")

    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    return datetime.datetime.strptime(string, fmt)


def chunks(candidates: List[Any], chunk_size: int) -> Iterator[List[Any]]:
    """
    Generator for n-sized chunks of list *L*.
    """
    if chunk_size is None or chunk_size == 0:
        raise ValueError(f"Parameter chunk_size: Unexpected value {chunk_size}.")

    if not isinstance(candidates, list):
        raise TypeError(f"Parameter L: Expected type list, got type {type(candidates)}.")

    if not isinstance(chunk_size, int):
        raise TypeError(f"Parameter chunk_size: Expected type int, got type {type(chunk_size)}.")

    for i in range(0, len(candidates), chunk_size):
        yield candidates[i: i + chunk_size]


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
