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
import asyncio
from typing import List, Dict, Optional

from prov.model import ProvDocument, ProvElement, PROV_REC_CLS, ProvActivity, ProvEntity
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

    def compute_graph(self, url: str, agent_mapping: Optional[Dict[str, List[str]]] = None) -> ProvDocument:
        """
        Compute gitlab2prov provenance graph for project at *url*.

        Unify and merge agents according to *agent_mapping*.
        """
        if agent_mapping is None:
            agent_mapping = {}
        sub_graphs = self._run_pipes(url)
        graph = self.unite_graphs(sub_graphs)
        graph = self._unite_agents(graph, agent_mapping)
        graph = self._project_unique_ids(graph, url)
        return graph

    def _unite_agents(self, graph: ProvDocument, agent_mapping: Dict[str, List[str]]) -> ProvDocument:
        """
        Compute and apply id mapping to unite agents according to *agent_mapping.*
        """
        id_mapping = {}
        for node in graph.get_records(ProvElement):
            name = agent_mapping.get({k.localpart: v for k, v in node.attributes}.get("user_name"))
            if name is None:
                id_mapping[node.identifier] = node.identifier
                continue
            namespace = node.identifier.namespace
            localpart = f"user-{name}"
            id_mapping[node.identifier] = QualifiedName(namespace, q_name(localpart))
        graph = self._apply_id_mapping(graph, id_mapping)
        return graph

    def _project_unique_ids(self, graph: ProvDocument, url: str) -> ProvDocument:
        """
        Compute and apply id mapping for project unique ids for entities and activities.
        """
        project = url_encoded_path(url).replace("%2F", "/")
        id_mapping = {}
        for record in graph.get_records(ProvElement):
            if not isinstance(record, (ProvActivity, ProvEntity)):
                id_mapping[record.identifier] = record.identifier
                continue
            namespace = record.identifier.namespace
            localpart = f"{project}-{record.identifier.localpart}"
            id_mapping[record.identifier] = QualifiedName(namespace, q_name(localpart))
        graph = self._apply_id_mapping(graph, id_mapping)
        return graph

    @staticmethod
    def _apply_id_mapping(graph: ProvDocument, id_mapping: Dict[QualifiedName, QualifiedName]) -> ProvDocument:
        """
        Compute prov graph where node id's have been updated with the provided by the id mapping.
        """
        records = []
        for record in graph.get_records():
            prov_type = PROV_REC_CLS[record.get_type()]
            if record.is_element():
                record = prov_type(record.bundle, id_mapping[record.identifier], record.attributes)
                records.append(record)
            else:
                (s_type, source), (t_type, target) = record.formal_attributes[:2]
                attributes = [(s_type, id_mapping[source]), (t_type, id_mapping[target])]
                attributes.extend(record.formal_attributes[2:])
                attributes.extend(record.extra_attributes)
                records.append(prov_type(record.bundle, record.identifier, attributes))
        mapping_applied = ProvDocument(records)
        mapping_applied = enforce_uniqueness_constraints(mapping_applied)
        return mapping_applied

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
