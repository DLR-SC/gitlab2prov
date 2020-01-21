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


import os
from configparser import ConfigParser


CONFIG_PATH = "./config/config.ini"

VALID_CONFIG = {
        "GITLAB":
        [
            "token",
            "rate",
            "project"
        ],
        "NEO4J":
        [
            "host",
            "user",
            "password"
        ]
    }

class ConfigurationException(Exception):
    pass

if not os.path.exists(CONFIG_PATH):
    raise ConfigurationException(f"Missing CONFIG file: {CONFIG_PATH}")

config = ConfigParser()
config.read(CONFIG_PATH)

CONFIG = config
TOKEN = config.get("GITLAB", "token")
PROJECT = config.get("GITLAB", "project")
RATE_LIMIT = int(config.get("GITLAB", "rate"))
NEO4J_HOST = config.get("NEO4J", "host")
NEO4J_USER = config.get("NEO4J", "user")
NEO4J_PASSWORD = config.get("NEO4J", "password")
NEO4J_BOLT_PORT = config.get("NEO4J", "bolt port")

for section in VALID_CONFIG.keys():
    if section not in CONFIG.sections():
        raise ConfigurationException(f"Section {section} is missing!")
    for param in VALID_CONFIG[section]:
        if param not in CONFIG[section]:
            raise ConfigurationException(f"Parameter {param} in section {section} is missing!")
