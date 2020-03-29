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
from gl2p.utils import serialize, store_in_db, unite, url_encoded_path

Pipeline = Union[
    CommitPipeline,
    CommitResourcePipeline,
    IssueResourcePipeline,
    MergeRequestResourcePipeline
]


def run_pipes(pipes: List[Pipeline]) -> List[ProvDocument]:
    """
    Execute pipeline workflow.
    """
    models: List[ProvDocument] = []
    for pipe in pipes:
        data = asyncio.run(pipe.fetch())
        pkgs = pipe.process(*data)
        models.append(pipe.create_model(pkgs))
    return models


def main() -> None:
    """
    Main execution entry point.

    Workflow:
    - create pipelines for commit, commit resource, issue resource and merge request resource models
    - execute pipelines by fetching necessary data, processing data into packages and populating model graphs
    - unite graphs into one and output serialization in configured format to stdout
    - store graph in neo4j by passing it to prov-db-connector
    """
    # retrieve configuration details
    try:
        config = get_config()
    except ConfigurationError as ce:
        raise ce

    # url encoded project path (org/pslug) -> (org%2Fpslug)
    pid = url_encoded_path(config.project_url)

    # only one client to facilitate request caching
    client = GitLabAPIClient(config.project_url, config.token, config.rate_limit)

    pipes = [
        CommitPipeline(pid, client),
        CommitResourcePipeline(pid, client),
        IssueResourcePipeline(pid, client),
        MergeRequestResourcePipeline(pid, client)
    ]

    # execute pipelines
    # unite model graphs
    doc = unite(run_pipes(pipes))

    # print serialization to stdout
    if not config.quiet:
        print(serialize(doc, config.format))

    # store graph in neo4j
    if config.neo4j:
        try:
            store_in_db(doc, config)
        except KeyError as ke:
            # indicates that graph already exists in neo4j
            raise ke


if __name__ == "__main__":
    main()
