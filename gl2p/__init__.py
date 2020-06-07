# Copyright (c) 2019 German Aerospace Center (DLR/SC).
# All rights reserved.
#
# This file is part of gitlab2prov.
# gitlab2prov is licensed under the terms of the MIT License.
# SPDX short Identifier: MIT
#
# You may obtain a copy of the License at:
# https://opensource.org/licenses/MIT
#
# A command line tool to extract provenance data (PROV W3C)
# from GitLab hosted repositories aswell as
# to store the extracted data in a Neo4J database.
#
# code-author: Claas de Boer <claas.deboer@dlr.de>
import re
import json
import asyncio
from collections import namedtuple
from typing import List, Dict, Optional, Type, Tuple, Any

from prov.model import ProvDocument, PROV_REC_CLS, ProvActivity, ProvEntity, ProvRecord, ProvAgent, ProvRelation
from prov.identifier import QualifiedName
from prov.dot import prov_to_dot

from gl2p.models import enforce_uniqueness_constraints
from gl2p.api import GitlabAPIClient
from gl2p.config import get_config, ConfigurationError
from gl2p.pipelines import CommitPipeline, CommitResourcePipeline, IssueResourcePipeline, MergeRequestResourcePipeline
from gl2p.utils import store_in_db, q_name, url_encoded_path


class Gitlab2Prov:

    def __init__(self, token: str, rate_limit: int = 10,
                 use_commit_model: bool = True,
                 use_commit_resource_model: bool = True,
                 use_issue_resource_model: bool = True,
                 use_merge_request_resource_model: bool = True):

        self._token = token
        self._rate_limit = rate_limit

        self.pipes = []
        if use_commit_model:
            self.pipes.append(CommitPipeline())
        if use_commit_resource_model:
            self.pipes.append(CommitResourcePipeline())
        if use_issue_resource_model:
            self.pipes.append(IssueResourcePipeline())
        if use_merge_request_resource_model:
            self.pipes.append(MergeRequestResourcePipeline())

    @staticmethod
    def serialize(graph: ProvDocument, fmt: str = "json") -> str:
        if fmt == "dot":
            return str(prov_to_dot(graph))
        return str(graph.serialize(format=fmt))

    @staticmethod
    def unite_graphs(graphs: List[ProvDocument]) -> ProvDocument:
        """
        Unite graphs by updating accumulator with records from others.
        """
        acc = graphs[0]
        for sub_graph in graphs[1:]:
            acc.update(sub_graph)
        graph = enforce_uniqueness_constraints(acc)
        return graph

    @staticmethod
    def read_alias_mapping(fp: str) -> Dict[str, str]:
        """
        Read alias mapping at file path *fp*.    (name: alias1, alias2, ...)
        Rebuild as a mapping from alias to name: (alias1: name; alias2: name; ...)
        """
        if not fp:
            return {}
        with open(fp, "r") as mapping:
            data = mapping.read()
            obj = json.loads(data)
        aliases = {v: k for k, vs in obj.items() for v in vs}
        return aliases

    @staticmethod
    def clean_attrs(attributes: Dict[Any, Any], mapping: Dict[str, str]) -> Dict[Any, Any]:
        """
        Remove name mentions from strings.
        """
        pattern = r'@[a-z_]+'  # matches user mentions such as @foo_bar

        def replace(match_object):
            match = match_object.group().replace("\\", "")[1:]
            replacement = mapping.get(match, match)
            return replacement

        cleaned = {}
        aliases = sorted(mapping.keys(), key=len, reverse=True)
        for key, value in attributes.items():
            if not isinstance(value, str):
                cleaned[key] = value
                continue
            value = re.sub(pattern, replace, value)

            for alias in aliases:
                value = value.replace(alias, mapping[alias])
            cleaned[key] = value
        return cleaned

    @staticmethod
    def _update_aliases(g: ProvDocument, aliases: Dict[str, str]) -> Dict[str, str]:
        """
        Update mapping with agents that aren't present in the initial mapping.
        """
        for agent in g.get_records(ProvAgent):
            attrs = {k.localpart: v for k, v in agent.attributes}
            name = attrs["user_name"]
            if name not in aliases:
                aliases[name] = name
        return aliases

    @staticmethod
    def _pseudonymize_aliases(aliases: Dict[str, str]) -> Dict[str, str]:
        """
        Pseudonymize alias mapping by enumeration.
        """
        enum = {value: str(n) for n, value in enumerate(set(aliases.values()))}
        pseudonymized = {}
        for key, value in aliases.items():
            pseudonymized[key] = enum[value]
        return pseudonymized

    def compute_graph(self,
                      url: str,
                      alias_mapping_fp: str = "",
                      pseudonymize: bool = False) -> ProvDocument:
        """
        Compute gitlab2prov provenance graph for project at *url*.

        Unify and merge agents according to *agent_mapping*.
        """
        aliases = self.read_alias_mapping(alias_mapping_fp)

        sub_graphs = self._run_pipes(url)
        graph = self.unite_graphs(sub_graphs)
        graph = self.postprocess_graph(graph, url, aliases, pseudonymize)
        return graph

    def _run_pipes(self, url: str) -> List[ProvDocument]:
        """
        Run Pipelines for a given client.
        """
        client = GitlabAPIClient(url, self._token, self._rate_limit)
        graphs = []
        for pipe in self.pipes:
            data = asyncio.run(pipe.fetch(client))
            packages = pipe.process(*data)
            graphs.append(pipe.create_model(packages))
        return graphs

    def postprocess_graph(self, g, url: str, aliases: Dict[str, str], pseudonymize: bool = False) -> ProvDocument:
        """
        Unite agents based on alias_mapping.
        Compute global unique id's for activities and entities by prepending the project name
        to their respective id's. Add attribute containint project to activities and entities.
        """
        aliases = self._update_aliases(g, aliases)
        if pseudonymize:
            aliases = self._pseudonymize_aliases(aliases)

        project = url_encoded_path(url).replace("%2F", "/")

        agts, agt_ids = self._unite_agents(g, aliases, pseudonymize)
        ents, ent_ids = self._project_unique(g, project, aliases, pseudonymize, p_type=ProvEntity)
        acts, act_ids = self._project_unique(g, project, aliases, pseudonymize, p_type=ProvActivity)

        mapping = {**agt_ids, **act_ids, **ent_ids}
        relations = self._update_relations(g, mapping)

        return ProvDocument([*agts, *ents, *acts, *relations])


    def _unite_agents(self,
                      g: ProvDocument,
                      aliases: Dict[str, str],
                      pseudonymize: bool = False) -> Tuple[List[ProvAgent], Dict[Any, Any]]:
        """
        Unite agents based on *alias_mapping*. Pseudonymize agents by enumeration.
        """
        if not aliases:
            agents = [agent for agent in g.get_records(ProvAgent)]
            ids = {agent.identifier: agent.identifier for agent in g.get_records(ProvAgent)}
            return agents, ids

        agents, ids = set(), {}
        for agent in g.get_records(ProvAgent):
            attributes = {q_n.localpart: (val, q_n) for q_n, val in agent.attributes}

            name = aliases.get(
                attributes["user_name"][0],
                attributes["user_name"][0])

            id_, namespace = agent.identifier, agent.identifier.namespace
            ids[id_] = united_id = QualifiedName(namespace, q_name(f"user-{name}"))

            attributes = {q_n: val for val, q_n in attributes.values()}

            if pseudonymize:
                attributes = {"user_name": name}

            agents.add(ProvAgent(agent.bundle, united_id, attributes))

        return list(agents), ids

    def _project_unique(self,
                        g: ProvDocument,
                        project: str,
                        mapping: Dict[str, str],
                        pseudonymize: bool, p_type: Type[Any]) -> Tuple[List[Any], Dict[Any, Any]]:
        """
        Prepend project name to record id's for records of type *p_type*.
        Add project name to record attributes.
        """
        records, ids = [], {}

        for record in g.get_records(p_type):
            attributes = {k: v for k, v in record.attributes}
            if pseudonymize:
                attributes = self.clean_attrs(attributes, mapping)
            attributes["project"] = project

            id_ = record.identifier
            namespace, localpart = id_.namespace, id_.localpart
            ids[id_] = unique_id = QualifiedName(namespace, q_name(f"{project}-{localpart}"))
            records.append(p_type(record.bundle, unique_id, attributes))

        return records, ids

    def _update_relations(self, g: ProvDocument, id_mapping: Dict[str, str]) -> List[ProvRelation]:
        """
        Return list of relation with updated source and target id's according to *id_mapping*.
        """
        relations = []
        for relation in g.get_records(ProvRelation):
            (s_type, s), (t_type, t) = relation.formal_attributes[:2]  # edge source, target

            attributes = [(s_type, id_mapping.get(s, s)), (t_type, id_mapping.get(t, t))]
            attributes.extend(relation.formal_attributes[2:])
            attributes.extend(relation.extra_attributes)

            r_type = PROV_REC_CLS[relation.get_type()]
            relations.append(r_type(relation.bundle, relation.identifier, attributes))
        return relations
