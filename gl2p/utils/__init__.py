import argparse
import datetime
import urllib.parse
import uuid
from typing import Any, Iterator, List

from prov.dot import prov_to_dot
from prov.model import ProvDocument
from provdbconnector import Neo4jAdapter, ProvDb
from py2neo import Graph


def serialize(doc: ProvDocument, fmt: str) -> str:
    """
    Return serialization according to format string.
    Allow for dot serialization.
    """
    if fmt == "dot":
        return str(prov_to_dot(doc))
    return str(doc.serialize(format=fmt))


def bundle_exists(config: argparse.Namespace) -> bool:
    """
    Return whether a bundle for the given project_id is already in the graph.
    """
    project_id = url_encoded_path(config.project_url)
    g = Graph(
        uri=f"bolt://{config.neo4j_host}:{config.neo4j_boltport}",
        auth=(config.neo4j_user, config.neo4j_password)
    )
    return bool(g.run(
        "MATCH (bundle:Entity)" +
        "WHERE bundle.`meta:identifier` = " + f"'{project_id.replace('%2F', '-')}'" +
        "RETURN bundle.`meta:identifier`"
    ).forward())


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


def dot_to_file(doc: ProvDocument, file: str) -> None:
    """
    Write PROV graph in dot representation to a file.
    """
    with open(file, "w") as dot:
        print(prov_to_dot(doc), file=dot)


def unite(docs: List[ProvDocument]) -> ProvDocument:
    """
    Merge multiple prov documents into one.

    Remove duplicated entries.
    """
    d0 = docs[0]
    for doc in docs[1:]:
        d0.update(doc)
    return d0.unified()


def ptime(string: str) -> datetime.datetime:
    """
    Parse datetimestring to datetime object.
    """
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: expected type str, got type {type(string)}.")

    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    return datetime.datetime.strptime(string, fmt)


def chunks(L: List[Any], chunk_size: int) -> Iterator[List[Any]]:
    """
    Generator for n-sized chunks of list *L*.
    """
    if chunk_size is None or chunk_size == 0:
        raise ValueError(f"Parameter chunk_size: Unexpected value {chunk_size}.")

    if not isinstance(L, list):
        raise TypeError(f"Parameter L: Expected type list, got type {type(L)}.")

    if not isinstance(chunk_size, int):
        raise TypeError(f"Parameter chunk_size: Expected type int, got type {type(chunk_size)}.")

    for i in range(0, len(L), chunk_size):
        yield L[i: i+chunk_size]


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


def qname(string: str) -> str:
    """
    Return string representation of uuid5 of *string*.

    Creates unique identifiers.
    """
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: Expected type str, got type {type(string)}.")

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, string))
