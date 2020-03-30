"""
Configuration handling.

Every option can be configured by a command line flag.
Every option can be configured by a config file option.
Flag values take precendence over config file option values.

Config strategy:
- Parse command line arguments
- If config file exists, supplement args with config file values
- Check if minimum configuration has been provided
- Return configuration namespace
"""
import sys
import argparse
import configparser
import os
from distutils.util import strtobool
from typing import Any, Dict, List, Tuple

prog = "GitLab2PROV"
description = "Extract provenance information from GitLab projects."
epilog = "Consider visiting GitLab2PROV on GitHub: https://github.com/DLR-SC/gitlab2prov"


class ConfigurationError(Exception):
    pass


def get_config() -> argparse.Namespace:
    """
    Return configuration namespace.
    """
    args = parse_args()

    if os.path.exists(args.config_file):
        args = patch(args)

    if underconfigured(args):
        keys = underconfigured(args)
        pick = [
            ("option", "has"),
            ("options", "have")
        ][min(1, len(keys.split())-1)]
        raise ConfigurationError(f"Necessary config {pick[0]} {keys} {pick[1]} not been provided.")

    print_config_summary(args)
    return args


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(prog, None, description, epilog)

    basic = parser.add_argument_group("BASIC CONFIG")
    neo4j = parser.add_argument_group("NEO4J CONFIG")
    basic.add_argument("-p", "--project-url",
                       help="gitlab project url",
                       metavar="URL")
    basic.add_argument("-t", "--token",
                       help="gitlab api access token",
                       metavar="TOKEN")
    basic.add_argument("-r", "--rate-limit",
                       help="api client rate limit (in req/s)",
                       metavar="LIMIT",
                       type=int)
    basic.add_argument("-c", "--config-file",
                       help="config file path",
                       default="config/config.ini",
                       metavar="CONFIG")
    basic.add_argument("-f", "--format",
                       help="provenance output format",
                       choices=["provn", "json", "rdf", "xml", "dot"])
    basic.add_argument("-q", "--quiet",
                       help="suppress output to stdout",
                       action="store_true")
    neo4j.add_argument("--neo4j",
                       help="enable neo4j storage",
                       action="store_true")
    neo4j.add_argument("--neo4j-user",
                       help="neo4j username",
                       metavar="USERNAME")
    neo4j.add_argument("--neo4j-password",
                       help="neo4j password",
                       metavar="PASSWORD")
    neo4j.add_argument("--neo4j-host",
                       help="neo4j host",
                       metavar="HOST")
    neo4j.add_argument("--neo4j-boltport",
                       help="neo4j bolt protocol port",
                       metavar="PORT")
    return parser.parse_args()


def patch(args: argparse.Namespace) -> argparse.Namespace:
    """
    Try to patch missing flag values with values from config file.
    """
    for key, val in config_items(args.config_file):
        try:
            if not getattr(args, key) and val:
                setattr(args, key, val)
        except AttributeError as ae:
            raise ConfigurationError(f"Config file key '{key}' is not a valid configuration option.\n")

    args.neo4j = bool(strtobool(str(args.neo4j)))
    args.quiet = bool(strtobool(str(args.quiet)))
    args.rate_limit = int(args.rate_limit)

    return args


def underconfigured(args: argparse.Namespace) -> str:
    """
    Return string of missing keys if there are any.
    """
    necessary = ["project_url", "token", "format"]
    neo4j = ["neo4j_user", "neo4j_host", "neo4j_password", "neo4j_boltport"]

    if args.neo4j:
        necessary.extend(neo4j)

    missing = ""
    for key in necessary:
        if not getattr(args, key):
            missing = ", ".join((missing, f"'{key}'"))
    return missing[2:]


def config_items(path: str) -> List[Tuple[str, Any]]:
    """
    Return config file option, value pairs.
    """
    config = configparser.ConfigParser()
    config.read(path)

    res = []
    for section in config.sections():
        for opt, val in config.items(section):
            res.append((opt, val))
    return res


def print_config_summary(args: argparse.Namespace) -> None:
    print("Config summary:", file=sys.stderr)
    for key, val in vars(args).items():
        print(f"{key:14} -> {val}", file=sys.stderr)
