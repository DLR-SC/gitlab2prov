#!/usr/bin/env python

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
# A command line tool to extract provenance data (PROV W3C)
# from GitLab hosted repositories aswell as
# to store the extracted data in a Neo4J database.
#
# code-author: Claas de Boer <claas.deboer@dlr.de>

import asyncio
import argparse
from typing import List, Union
from provdbconnector import Neo4jAdapter, ProvDb
from prov.model import ProvDocument
from gl2p.config import get_config
from gl2p.api.gitlab import GitLabProjectWrapper
from gl2p.utils.helpers import url_encoded_path
from gl2p.pipelines import (CommitPipeline, CommitResourcePipeline,
                            IssueResourcePipeline, MergeRequestResourcePipeline)


Pipeline = Union[
    CommitPipeline,
    CommitResourcePipeline,
    IssueResourcePipeline,
    MergeRequestResourcePipeline
]


def unite_documents(documents: List[ProvDocument]) -> ProvDocument:
    """
    Merge multiple prov documents into one.

    Remove duplicated entries.
    """
    d0 = documents[0]

    for doc in documents[1:]:
        d0.update(doc)

    return d0.unified()


def run_pipes(pipelines: List[Pipeline]) -> List[ProvDocument]:
    """
    Execute pipelines.
    """
    models = []

    for pipe in pipelines:
        data = asyncio.run(pipe.fetch())
        resources = pipe.process(*data)
        models.append(pipe.create_model(resources))

    return models


def store_in_db(document: ProvDocument, config: argparse.Namespace) -> None:
    """
    Store prov document in neo4j instance.
    """
    auth_info = {
        "user_name": config.neo4j_user,
        "user_password": config.neo4j_password,
        "host": f"{config.neo4j_host}:{config.neo4j_boltport}"
        }

    prov_api = ProvDb(adapter=Neo4jAdapter, auth_info=auth_info)
    prov_api.save_document(document)


def main() -> None:
    """
    Main execution loop.
    """
    config = get_config()

    api_client = GitLabProjectWrapper(config.project_url, config.token, config.rate_limit)
    project_id = url_encoded_path(config.project_url)

    pipelines = [
        CommitPipeline(project_id, api_client),
        CommitResourcePipeline(project_id, api_client),
        IssueResourcePipeline(project_id, api_client),
        MergeRequestResourcePipeline(project_id, api_client)
    ]  # type: List[Pipeline]

    docs = run_pipes(pipelines)
    doc = unite_documents(docs)

    print(doc.serialize(format=config.format))

    # store in neo4j, if flag is set
    if config.neo4j:
        store_in_db(doc, config)


if __name__ == "__main__":
    main()
