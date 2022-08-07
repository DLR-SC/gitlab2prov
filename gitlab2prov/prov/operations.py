import json
import logging
import hashlib
from typing import Iterable, NamedTuple, Type

from collections import defaultdict, Counter
from pathlib import Path
from typing import Optional, Sequence, Any
from urllib.parse import urlencode

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


def serialize_graph(
    graph: ProvDocument, format: str = "json", destination=None, encoding="utf-8"
) -> str | None:
    if format not in SERIALIZATION_FORMATS:
        raise ValueError("Unsupported serialization format.")
    if format == "dot":
        return prov_to_dot(graph).to_string().encode(encoding)
    return graph.serialize(format=format, destination=destination)


def deserialize_graph(source: str = None, content: str = None):
    for format in DESERIALIZATION_FORMATS:
        try:
            return ProvDocument.deserialize(
                source=source, content=content, format=format
            )
        except:
            continue
    raise Exception


def format_stats_as_ascii_table(stats: dict[str, int]) -> str:
    table = f"|{'Record Type':20}|{'Count':20}|\n+{'-'*20}+{'-'*20}+\n"
    for record_type, count in stats.items():
        table += f"|{record_type:20}|{count:20}|\n"
    return table


def format_stats_as_csv(stats: dict[str, int]) -> str:
    csv = f"Record Type, Count\n"
    for record_type, count in stats.items():
        csv += f"{record_type}, {count}\n"
    return csv


def stats(
    graph: ProvDocument, resolution: str, formatter=format_stats_as_ascii_table
) -> str:
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


def combine(graphs: Iterable[ProvDocument]) -> ProvDocument:
    log.info(f"combine graphs {graphs}")
    try:
        acc = next(graphs)
    except StopIteration:
        return graph_factory()
    for graph in graphs:
        acc.update(graph)
    return dedupe(acc)




def dedupe(graph: ProvDocument) -> ProvDocument:
    log.info(f"deduplicate ProvElement's and ProvRelation's in {graph=}")
    graph = graph.unified()
    records = list(graph.get_records((ProvElement)))
    attrs = defaultdict(set)
    bundles = dict()

    for relation in graph.get_records(ProvRelation):
        rel = (type(relation), tuple(relation.formal_attributes))
        bundles[rel] = relation.bundle
        attrs[rel].update(relation.extra_attributes)

    for rel in attrs:
        bundle = bundles[rel]
        rtype, formal_attributes = rel
        attributes = list(formal_attributes)
        attributes.extend(attrs[rel])
        records.append(rtype(bundle, None, attributes))
    return graph_factory(records)


def read(fp: Path) -> dict[str, list[str]]:
    with open(fp, "r") as f:
        data = f.read()
        d = json.loads(data)
    if not d:
        log.info(f"empty agent mapping")
        return dict()
    return d


def xform(d: dict[str, list[str]]) -> dict[str, str]:
    return {alias: name for name, aliases in d.items() for alias in aliases}


def uncover_name(agent: str, names: dict[str, str]) -> tuple[QualifiedName, str]:
    [(qn, name)] = [
        (key, val) for key, val in agent.attributes if key.localpart == "name"
    ]
    return qn, names.get(name, name)


def uncover_double_agents(graph: ProvDocument, fp: str) -> ProvDocument:
    log.info(f"resolve aliases in {graph=}")
    # read mapping & transform
    names = xform(read(fp))
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
        formal = [
            (key, reroute.get(val, val)) for key, val in relation.formal_attributes
        ]
        extra = [(key, reroute.get(val, val)) for key, val in relation.extra_attributes]
        r_type = PROV_REC_CLS.get(relation.get_type())
        records.append(r_type(relation.bundle, relation.identifier, formal + extra))

    return graph_factory(records).unified()


def get_username(agent: ProvAgent) -> str | None:
    names = list(agent.get_attribute(USERNAME))
    return names[0] if names else None


def get_usermail(agent: ProvAgent) -> str | None:
    emails = list(agent.get_attribute(USEREMAIL))
    return emails[0] if emails else None


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
        name = get_username(agent)
        mail = get_usermail(agent)

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
        formal = [
            (key, pseudonyms.get(val, val)) for key, val in relation.formal_attributes
        ]
        extra = [
            (key, pseudonyms.get(val, val)) for key, val in relation.extra_attributes
        ]
        r_type = PROV_REC_CLS.get(relation.get_type())
        records.append(r_type(relation.bundle, relation.identifier, formal + extra))

    return graph_factory(records)
