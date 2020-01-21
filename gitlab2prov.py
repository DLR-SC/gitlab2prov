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

from provdbconnector import Neo4jAdapter, ProvDb

from gl2p.config import CONFIG, PROJECT, TOKEN, RATE_LIMIT
from gl2p.gitlab import ProjectWrapper
from gl2p.pipelines import CommitPipeline, CommitResourcePipeline


def main(provn, neo4j):
    c = ProjectWrapper(PROJECT, TOKEN, RATE_LIMIT)

    print(f"Generating PROV document for {PROJECT} at {RATE_LIMIT} req/sec")
    
    pipelines = [
        CommitPipeline(c),
        CommitResourcePipeline(c)
    ]

    docs = []
    for pipe in pipelines:
        data = asyncio.run(pipe.fetch())
        processed = pipe.process(*data)
        document = pipe.create_model(processed)
        docs.append(document)

    document, *remaining = docs
    for doc in remaining:
        document.update(doc)

    document = document.unified()
    
    provn = provn if provn else "out.provn"

    with open(f"{provn}", "w") as f:
        print(document.get_provn(), file=f) 
    
    if not neo4j:
        return

    auth_info = {
        "user_name": CONFIG["NEO4J"]["user"],
        "user_password": CONFIG["NEO4J"]["password"],
        "host": f"{CONFIG['NEO4J']['host']}:{CONFIG['NEO4J']['boltport']}"
        }

    prov_api = ProvDb(adapter=Neo4jAdapter, auth_info=auth_info)
    prov_api.save_document(document)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract provenance information from a GitLab repository.")
    parser.add_argument("--provn", help="output file")
    parser.add_argument("--neo4j", help="save to neo4j", action="store_true")
    args = parser.parse_args()
    main(args.provn, args.neo4j)
