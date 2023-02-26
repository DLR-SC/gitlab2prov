import json
import sys
import logging
import hashlib
from typing import NamedTuple, Type

from collections import defaultdict, Counter
from pathlib import Path
from typing import Optional, Sequence, Any
from urllib.parse import urlencode

from ruamel.yaml import YAML
from prov.dot import prov_to_dot
from prov.identifier import QualifiedName
from prov.model import (
    ProvDocument,
    ProvRecord,
    ProvElement,
    ProvRelation,
    ProvAgent,
    ProvEntity,
    ProvActivity,
    PROV_ROLE,
    PROV_TYPE,
    PROV_REC_CLS,
)


log = logging.getLogger(__name__)


USERNAME = "name"
USEREMAIL = "email"
SERIALIZATION_FORMATS = ["json", "xml", "rdf", "provn", "dot"]
DESERIALIZATION_FORMATS = ["rdf", "xml", "json"]


def read_provenance_file(filename: str) -> ProvDocument:
    """Read provenance document from file or sys.stdin."""
    if filename == "-":
        content = sys.stdin.read()
    else:
        with open(filename, "r") as f:
            content = f.read()
    return deserialize_string(content=content)


def deserialize_string(content: str, format: str = None):
    """Deserialize a ProvDocument from a string."""
    for format in DESERIALIZATION_FORMATS:
        try:
            doc = ProvDocument.deserialize(content=content, format=format)
            return doc
        except Exception:
            pass
    raise Exception(f"Deserialization failed for {content=}, {format=}")


def write_provenance_file(
    document: ProvDocument, filename: str, format: str = "json", overwrite: bool = True
):
    """Write provenance document to file."""
    if Path(filename).exists() and not overwrite:
        raise FileExistsError(f"File {filename} already exists.")
    with open(filename, "w") as f:
        f.write(serialize_string(document, format=format))


def serialize_string(document: ProvDocument, format: str = "json") -> str:
    """Serialize a ProvDocument to a string."""
    if format not in SERIALIZATION_FORMATS:
        raise ValueError("Unsupported serialization format.")
    if format != "dot":
        return document.serialize(format=format)
    return prov_to_dot(document).to_string()


def format_stats_as_ascii_table(stats: dict[str, int]) -> str:
    table = f"|{'Record Type':20}|{'Count':20}|\n+{'-'*20}+{'-'*20}+\n"
    for record_type, count in stats.items():
        table += f"|{record_type:20}|{count:20}|\n"
    return table


def format_stats_as_csv(stats: dict[str, int]) -> str:
    csv = "Record Type, Count\n"
    for record_type, count in stats.items():
        csv += f"{record_type}, {count}\n"
    return csv


def stats(graph: ProvDocument, resolution: str, format: str = "table") -> str:
    if format == "csv":
        formatter = format_stats_as_csv
    if format == "table":
        formatter = format_stats_as_ascii_table

    elements = Counter(e.get_type().localpart for e in graph.get_records(ProvElement))
    relations = Counter(r.get_type().localpart for r in graph.get_records(ProvRelation))

    stats = dict(sorted(elements.items()))
    if resolution == "coarse":
        stats.update({"Relations": relations.total()})
    if resolution == "fine":
        stats.update(sorted(relations.items()))
    return formatter(stats)


def qualified_name(localpart: str) -> QualifiedName:
    namespace = graph_factory().get_default_namespace()
    return QualifiedName(namespace, localpart)


def graph_factory(records: Optional[Sequence[ProvRecord]] = None) -> ProvDocument:
    if records is None:
        records = []
    graph = ProvDocument(records)
    graph.set_default_namespace("http://github.com/dlr-sc/gitlab2prov/")
    return graph


def combine(*documents: ProvDocument) -> ProvDocument:
    log.info(f"combine {documents=}")
    acc = documents[0]
    for document in documents[1:]:
        acc.update(document)
    return dedupe(acc)


class StrippedRelation(NamedTuple):
    s: QualifiedName
    t: QualifiedName
    type: Type[ProvRelation]


def dedupe(graph: ProvDocument) -> ProvDocument:
    log.info(f"deduplicate ProvElement's and ProvRelation's in {graph=}")
    graph = graph.unified()
    records = list(graph.get_records((ProvElement)))

    bundles = dict()
    attributes = defaultdict(set)

    for relation in graph.get_records(ProvRelation):
        stripped = StrippedRelation(
            relation.formal_attributes[0],
            relation.formal_attributes[1],
            PROV_REC_CLS[relation.get_type()],
        )
        bundles[stripped] = relation.bundle
        attributes[stripped].update(relation.extra_attributes)

    records.extend(
        relation.type(
            bundles[relation],
            None,
            [relation.s, relation.t] + list(attributes[relation]),
        )
        for relation in attributes
    )
    return graph_factory(records)


def read(fp: Path) -> dict[str, list[str]]:
    with open(fp, "r") as f:
        data = f.read()
        d = json.loads(data)
    if not d:
        log.info("empty agent mapping")
        return dict()
    return d


def read_duplicated_agent_mapping(fp: str):
    """Mapping that maps user names to a list of their aliases."""
    with open(fp, "rt") as f:
        yaml = YAML(type="safe")
        agents = yaml.load(f.read())
    return {agent["name"]: agent["aliases"] for agent in agents}


def build_inverse_index(mapping):
    """Build the inverse index for a double agent mapping."""
    return {alias: name for name, aliases in mapping.items() for alias in aliases}


def uncover_name(agent: str, names: dict[str, str]) -> tuple[QualifiedName, str]:
    [(qn, name)] = [(key, val) for key, val in agent.attributes if key.localpart == "name"]
    return qn, names.get(name, name)


def merge_duplicated_agents(graph, path_to_mapping):
    log.info(f"resolve aliases in {graph=}")
    mapping = read_duplicated_agent_mapping(path_to_mapping)
    names = build_inverse_index(mapping)

    # dict to temporarily store agent attributes
    attrs = defaultdict(set)
    # map of old agent identifiers to new agent identifiers
    # used to reroute relationships
    reroute = dict()
    # prov records that are not affected by this operation
    records = list(graph.get_records((ProvEntity, ProvActivity)))

    for agent in graph.get_records(ProvAgent):
        # resolve the agent alias (uncover its identity)
        name = uncover_name(agent, names)
        # rebuild the attributes of the current agent
        # start by adding the uncovered given name
        attrs[name].add(name)
        # add all other attributes aswell
        attrs[name].update(t for t in agent.attributes if t[0].localpart != "name")

        repr_attrs = [tpl for tpl in attrs[name] if tpl[1] in ("name", "email")]
        identifier = qualified_name(f"User?{urlencode(repr_attrs)}")
        records.append(ProvAgent(agent.bundle, identifier, attrs[name]))

        reroute[agent.identifier] = identifier

    for relation in graph.get_records(ProvRelation):
        formal = [(key, reroute.get(val, val)) for key, val in relation.formal_attributes]
        extra = [(key, reroute.get(val, val)) for key, val in relation.extra_attributes]
        r_type = PROV_REC_CLS.get(relation.get_type())
        records.append(r_type(relation.bundle, relation.identifier, formal + extra))

    return graph_factory(records).unified()


def get_attribute(record: ProvRecord, attribute: str, first: bool = True) -> str | None:
    choices = list(record.get_attribute(attribute))
    if not choices:
        return
    return choices[0] if first else choices


def pseudonymize_agent(
    agent: ProvAgent,
    identifier: QualifiedName,
    keep: list[QualifiedName],
    replace: dict[str, Any],
) -> ProvAgent:
    kept = [(key, val) for key, val in agent.extra_attributes if key in keep]
    replaced = [
        (key, replace.get(key.localpart, val))
        for key, val in agent.extra_attributes
        if key.localpart in replace
    ]
    return ProvAgent(agent.bundle, identifier, kept + replaced)


def pseudonymize(graph: ProvDocument) -> ProvDocument:
    log.info(f"pseudonymize agents in {graph=}")

    # get all records except for agents and relations
    records = list(graph.get_records((ProvActivity, ProvEntity)))

    pseudonyms = dict()
    for agent in graph.get_records(ProvAgent):
        name = get_attribute(agent, USERNAME)
        mail = get_attribute(agent, USEREMAIL)

        if name is None:
            raise ValueError("ProvAgent representing a user has to have a name!")

        # hash name & mail if present
        namehash = hashlib.sha256(bytes(name, "utf-8")).hexdigest()
        mailhash = hashlib.sha256(bytes(mail, "utf-8")).hexdigest() if mail else None
        # create a new id as a pseudonym using the hashes
        pseudonym = qualified_name(f"User?name={namehash}&email={mailhash}")

        # map the old id to the pseudonym
        pseudonyms[agent.identifier] = pseudonym

        # keep only prov role & prov type
        # replace name & mail with hashes
        pseudonymized = pseudonymize_agent(
            agent,
            identifier=pseudonym,
            keep=[PROV_ROLE, PROV_TYPE],
            replace={USERNAME: namehash, USEREMAIL: mailhash},
        )
        # add pseudonymized agent to the list of records
        records.append(pseudonymized)

    # replace old id occurences with the pseudonymized id
    for relation in graph.get_records(ProvRelation):
        formal = [(key, pseudonyms.get(val, val)) for key, val in relation.formal_attributes]
        extra = [(key, pseudonyms.get(val, val)) for key, val in relation.extra_attributes]
        r_type = PROV_REC_CLS.get(relation.get_type())
        records.append(r_type(relation.bundle, relation.identifier, formal + extra))

    return graph_factory(records)
