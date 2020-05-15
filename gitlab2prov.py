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

from gl2p import Gitlab2Prov
from gl2p.config import get_config


def main():
    config = get_config()

    glp = Gitlab2Prov(config.token, config.rate_limit)
    projects = [glp.compute_graph(project) for project in config.project_urls]
    graph = glp.unite_graphs(projects)

    if not config.quiet:
        print(glp.serialize(graph, fmt=config.format))


if __name__ == "__main__":
    main()
