import argparse
import datetime
import urllib.parse
import uuid
from typing import Any, Iterator, List
from collections import defaultdict

from prov.identifier import QualifiedName
from prov.dot import prov_to_dot
from prov.model import ProvDocument, PROV_REC_CLS, ProvElement, ProvAgent, ProvEntity, ProvRelation, ProvActivity
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


def prepare_project_graph(graph: ProvDocument, project_url: str, agent_mapping=None) -> ProvDocument:
    """
    Create global id's for project activities and entities.
    Merge agents based on agent mapping.

    *agent_mapping* is a mapping from a name to name versions (aliases).
    For example user "Robert Andrews" could have the git name "Bobby101" and the GitLab username "Andrews, Bob"
    This would lead to two agents, one with name "Bobby101" and another with the name "Andrews, Bob".
    To unify them, the mapping provides a name that should be the name for both of them.

    For example:
        agent_mapping = {"Robert Andrews": ["Andrews, Bob", "Bobby101"]}

    This should lead to one agent with the name "Robert Andrews" and all properties
    of the agents of names "Bobby101" and "Andrews, Bob".
    """
    if agent_mapping is None:
        agent_mapping = {}

    project_name = url_encoded_path(project_url).replace("%2F", "-")

    processed, id_mapping = [], {}
    agent_mapping = {value: key for key, values in agent_mapping.items() for value in values}

    for element in graph.get_records(ProvElement):
        if isinstance(element, ProvAgent):
            name = {k.localpart: v for k, v in element.attributes}["user_name"]
            if name not in agent_mapping:
                # no merge necessary
                id_mapping[element.identifier] = element.identifier
                processed.append(element)
            else:
                # update agent id to the new name provided by the agent mapping
                # will allow to filter duplicates by a call to graph.unified()
                _id = QualifiedName(element.identifier.namespace, f"user-{agent_mapping[name]}")
                id_mapping[element.identifier] = _id
                processed.append(ProvAgent(element.bundle, _id, element.attributes))

        elif isinstance(element, (ProvActivity, ProvEntity)):
            _id = QualifiedName(element.identifier.namespace, q_name(f"{project_name}-{element.identifier.localpart}"))
            id_mapping[element.identifier] = _id
            processed.append(PROV_REC_CLS[element.get_type()](element.bundle, _id, element.attributes))

    # update relations to incorporate new element id's
    for relation in graph.get_records(ProvRelation):
        (s_type, source), (t_type, target) = relation.formal_attributes[:2]
        attributes = [(s_type, id_mapping[source]), (t_type, id_mapping[target])]
        attributes.extend(relation.formal_attributes[2:])
        attributes.extend(relation.extra_attributes)
        processed.append(PROV_REC_CLS[relation.get_type()](relation.bundle, relation.identifier, attributes))

    return ProvDocument(processed)


def remove_duplicates(graph: ProvDocument) -> ProvDocument:
    """
    Remove duplicate relations that have the same type, source and target.
    """
    new_records = list(graph.get_records(ProvElement))
    duplicates = defaultdict(set)  # type -> set(tuple(source, target))

    for relation in graph.get_records(ProvRelation):
        (_, source), (_, target) = relation.formal_attributes[:2]
        if type(relation) in duplicates:
            if (source, target) not in duplicates[type(relation)]:
                # no relation of this type between source and target before
                # therefore add this relation to the graph
                new_records.append(relation)
        else:
            new_records.append(relation)
        duplicates[type(relation)].add((source, target))  # add rel to record of duplicate
    return ProvDocument(new_records)


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
