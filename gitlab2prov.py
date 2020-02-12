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

import argparse
import asyncio
from typing import List, Union
from provdbconnector import Neo4jAdapter, ProvDb
from prov.model import ProvDocument
from gl2p.config import CONFIG, PROJECT, RATE_LIMIT, TOKEN
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


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Extract provenance information from a GitLab repository."
    )

    parser.add_argument("--provn", help="output file")
    parser.add_argument("--config", help="specify config file path")
    parser.add_argument("--neo4j", help="save to neo4j", action="store_true")

    return parser.parse_args()


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


def write_to_file(document: ProvDocument, provn: str, project_id: str) -> None:
    """
    Write prov document in PROVN notation to *outfile*.
    """
    outfile = ""

    if provn:
        if not provn.endswith(".provn"):
            outfile = provn + ".provn"
        else:
            outfile = provn
    else:
        outfile = f"{project_id.replace('%2F', '-')}.provn"

    with open(outfile, "w") as f:
        print(document.get_provn(), file=f)


def store_in_db(document: ProvDocument) -> None:
    """
    Store prov document in neo4j instance.
    """
    auth_info = {
        "user_name": CONFIG["NEO4J"]["user"],
        "user_password": CONFIG["NEO4J"]["password"],
        "host": f"{CONFIG['NEO4J']['host']}:{CONFIG['NEO4J']['boltport']}"
        }

    prov_api = ProvDb(adapter=Neo4jAdapter, auth_info=auth_info)
    prov_api.save_document(document)


def main() -> None:
    """
    Main execution loop.

    Create api wrapper instance, pass it to each pipeline.
    Run pipeline execution flows (fetch, process, create_model).
    Merge resulting prov documents.

    Write united document in PROVN notation to file.
    Store united document in Neo4j if appropriate flag is set.
    """
    args = parse_args()
    provn, neo4j = args.provn, args.neo4j

    api_client = GitLabProjectWrapper(PROJECT, TOKEN, RATE_LIMIT)
    project_id = url_encoded_path(PROJECT)

    pipelines = [
        CommitPipeline(project_id, api_client),
        CommitResourcePipeline(project_id, api_client),
        IssueResourcePipeline(project_id, api_client),
        MergeRequestResourcePipeline(project_id, api_client)
    ]  # type: List[Pipeline]

    docs = run_pipes(pipelines)
    doc = unite_documents(docs)

    write_to_file(doc, provn, project_id)

    if neo4j:
        store_in_db(doc)


if __name__ == "__main__":
    main()
