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


# standard lib imports
import os
from configparser import ConfigParser
# third party imports
# local imports
from gl2p.commons import ConfigurationException


CONFIG_PATH = "config/config.ini"
VALID_CONFIG = {
        "GITLAB":
        [
            "token",
            "url",
            "project"
        ],
        "NEO4J":
        [
            "host",
            "user",
            "password"
        ]
    }

if not os.path.exists(CONFIG_PATH):
    raise ConfigurationException(f"Missing CONFIG file: {CONFIG_PATH}")

CONFIG = ConfigParser()
CONFIG.read(CONFIG_PATH)

for section in VALID_CONFIG.keys():
    if section not in CONFIG.sections():
        raise ConfigurationException(f"Section {section} is missing!")
    for param in VALID_CONFIG[section]:
        if param not in CONFIG[section]:
            raise ConfigurationException(f"Parameter {param} in section {section} is missing!")
# TODO: also check types of content ?
