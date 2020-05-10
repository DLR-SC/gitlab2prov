#!/usr/bin/env python3
# Copyright (c) 2019-2020 German Aerospace Center (DLR/SC).
# All rights reserved.
#
# This file is part of gitlab2prov.
# gitlab2prov is licensed under the terms of the MIT License.
# SPDX short Identifier: MIT
#
# You may obtain a copy of the License at:
# https://opensource.org/licenses/MIT
#
# GitLab2PROV is a command line tool to extract provenance data (W3C PROV)
# from GitLab hosted repositories aswell as
# to store the extracted data in a Neo4J database.
#
# code-author: Claas de Boer <claas.deboer@dlr.de>
import asyncio
from typing import List, Union

from prov.model import ProvDocument

from gl2p.api import GitLabAPIClient
from gl2p.config import ConfigurationError, get_config
from gl2p.pipelines import (CommitPipeline, CommitResourcePipeline,
                            IssueResourcePipeline,
                            MergeRequestResourcePipeline)
from gl2p.utils import serialize, store_in_db, unite, prepare_project_graph, remove_duplicates


Pipeline = Union[
    CommitPipeline,
    CommitResourcePipeline,
    IssueResourcePipeline,
    MergeRequestResourcePipeline
]


def run_pipes(pipes: List[Pipeline], client: GitLabAPIClient) -> List[ProvDocument]:
    """
    Execute pipeline workflow.
    """
    graphs: List[ProvDocument] = []
    for pipe in pipes:
        data = asyncio.run(pipe.fetch(client))
        packages = pipe.process(*data)
        graphs.append(pipe.create_model(packages))
    return graphs


def compute_graphs(projects: List[str], token: str, rate_limit: int) -> List[ProvDocument]:
    """
    Compute graph for each project url.
    Apply agent mapping to each graph.
    Add project name to node attributes.
    """
    pipes = [CommitPipeline(), CommitResourcePipeline(), IssueResourcePipeline(), MergeRequestResourcePipeline()]
    graphs = []
    for url in projects:
        client = GitLabAPIClient(url, token, rate_limit)
        models = run_pipes(pipes, client)
        united_model = unite(models)
        project_graph = prepare_project_graph(united_model, project_url=url, agent_mapping={})
        graphs.append(project_graph)
    return graphs


def unite_project_graphs(graphs: List[ProvDocument]) -> ProvDocument:
    """
    Unite multiple project graphs into one.
    """
    acc = graphs[0]
    for graph in graphs[1:]:
        acc.update(graph)
    cleaned = remove_duplicates(acc)
    return cleaned


def main() -> None:
    """
    Main execution entry point.

    Workflow:
    - get config details
    - create pipelines for commit, commit resource, issue resource and merge request resource models
    - execute pipelines by fetching necessary data, processing data into packages and populating model graphs
    - unite graphs into one and output serialization in configured format to stdout
    - store graph in neo4j by passing it to prov-db-connector
    """
    try:
        config = get_config()
    except ConfigurationError as ce:
        raise ce

    # compute graph for each project url
    # apply agent mapping
    project_graphs = compute_graphs(config.project_urls, config.token, config.rate_limit)

    # unite project graphs
    graph = unite_project_graphs(project_graphs)

    # print serialization to stdout
    if not config.quiet:
        print(serialize(graph, config.format))

    # store graph in neo4j
    if config.neo4j:
        try:
            store_in_db(graph, config)
        except KeyError as ke:
            # indicates that graph already exists in neo4j
            raise ke


if __name__ == "__main__":
    main()
