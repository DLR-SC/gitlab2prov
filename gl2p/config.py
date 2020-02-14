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
import argparse
import configparser
from typing import Dict, Any


class ConfigurationException(Exception):
    pass


def get_config() -> argparse.Namespace:
    """
    Return configuration Namespace.
    """
    # dictionary of arguments
    args = vars(parse_args())

    if not os.path.exists(args["config_file"]):
        raise ConfigurationException(f"Missing config file: {args['config_file']}")

    config = configparser.ConfigParser()
    config.read(args["config_file"])

    del args["config_file"]

    # path missing values with once from config file
    args = patch_args(args, config)

    # convert to int
    args["rate_limit"] = int(args["rate_limit"])

    # convert back to namespace
    return argparse.Namespace(**args)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Extract provenance information from GitLab projects.",
        epilog="Consider visiting GitLab2PROV on GitHub: https://github.com/DLR-SC/gitlab2prov"
    )

    basic = parser.add_argument_group("BASIC CONFIG")
    basic.add_argument("-p", "--project-url", help="gitlab project url", metavar="URL")
    basic.add_argument("-t", "--token", help="gitlab api access token", metavar="TOKEN")
    basic.add_argument(
        "-r", "--rate-limit",
        help="api client rate limit (in req/s)",
        metavar="LIMIT",
        type=int
    )
    basic.add_argument(
        "-c", "--config-file",
        help="config file path",
        default="config/config.ini",
        metavar="CONFIG"
    )
    basic.add_argument(
        "-f", "--format",
        help="provenance output format",
        choices=["provn", "json", "rdf", "xml"]
    )

    neo4j = parser.add_argument_group("NEO4J CONFIG")
    neo4j.add_argument("--neo4j", help="enable neo4j storage", action="store_true")
    neo4j.add_argument("--neo4j-user", help="neo4j username", metavar="USERNAME")
    neo4j.add_argument("--neo4j-password", help="neo4j password", metavar="PASSWORD")
    neo4j.add_argument("--neo4j-host", help="neo4j host", metavar="HOST")
    neo4j.add_argument("--neo4j-boltport", help="neo4j bolt protocol port", metavar="PORT")

    return parser.parse_args()


def patch_args(args: Dict[str, Any], config: configparser.ConfigParser) -> Dict[str, Any]:
    """
    Fill missing values of args with values from config file.

    Command line arguments, if given, take precedence.
    Sets default values for optional flags such as --format and --rate-limit.
    Raise exception if required values are missing.
    """
    required = ["project_url", "token", "neo4j_user", "neo4j_password", "neo4j_host", "neo4j_boltport"]

    if not args["neo4j"]:
        to_be_removed = ["neo4j_user", "neo4j_password", "neo4j_host", "neo4j_boltport"]
        for key in to_be_removed:
            required.remove(key)
            del args[key]

    # refill keys from config if empty
    for key in args.keys():

        if key == "neo4j":
            # skip neo4j flag
            continue

        if not args[key]:

            if key in required and key not in config["GITLAB2PROV"]:
                # key not in config file
                raise ConfigurationException(f"Config argument {key} is necessary, though no value has been given.")

            if key not in required:
                # default values for optional flags
                if key == "format":
                    args[key] = config.get("GITLAB2PROV", key, fallback="provn")
                    continue
                if key == "rate_limit":
                    args[key] = config.get("GITLAB2PROV", key, fallback=10)
                    continue

            args[key] = config.get("GITLAB2PROV", key)

    return args
