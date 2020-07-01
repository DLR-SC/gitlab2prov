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
import argparse
import configparser
import os
import sys
from distutils.util import strtobool
from typing import Any, List, Tuple

prog = "GitLab2PROV"
description = "Extract provenance information from GitLab projects."
epilog = "Consider visiting GitLab2PROV on GitHub: https://github.com/DLR-SC/gitlab2prov"


class ConfigurationError(Exception):
    pass


def get_config() -> argparse.Namespace:
    """Return configuration namespace."""
    args = parse_args()

    if os.path.exists(args.config_file):
        args = patch(args)

    if is_under_configured(args):
        keys = is_under_configured(args)
        pick = [
            ("option", "has"),
            ("options", "have")
        ][min(1, len(keys.split())-1)]
        raise ConfigurationError(f"Necessary config {pick[0]} {keys} {pick[1]} not been provided.")

    return args


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog, None, description, epilog)

    basic = parser.add_argument_group("BASIC CONFIG")
    neo4j = parser.add_argument_group("NEO4J CONFIG")
    basic.add_argument("-p", "--project-urls",
                       help="gitlab project urls", nargs="+", metavar="<string>")
    basic.add_argument("-t", "--token",
                       help="gitlab api access token", metavar="<string>")
    basic.add_argument("-r", "--rate-limit",
                       help="api client rate limit (in req/s)", metavar="<int>", type=int)
    basic.add_argument("-c", "--config-file",
                       help="config file path", default="config/config.ini", metavar="<string>")
    basic.add_argument("-f", "--format",
                       help="provenance output format", choices=["provn", "json", "rdf", "xml", "dot"])
    basic.add_argument("-q", "--quiet",
                       help="suppress output to stdout", action="store_true")
    basic.add_argument("--aliases", metavar="<string>",
                       help="path to agent alias mapping json file")
    basic.add_argument("--pseudonymize", action="store_true",
                       help="pseudonymize agents")
    neo4j.add_argument("--neo4j",
                       help="enable neo4j storage", action="store_true")
    neo4j.add_argument("--neo4j-user",
                       help="neo4j username", metavar="<string>")
    neo4j.add_argument("--neo4j-password",
                       help="neo4j password", metavar="<string>")
    neo4j.add_argument("--neo4j-host",
                       help="neo4j host", metavar="<string>")
    neo4j.add_argument("--neo4j-boltport",
                       help="neo4j bolt protocol port", metavar="<string>")
    return parser.parse_args()


def patch(args: argparse.Namespace) -> argparse.Namespace:
    """Try to patch missing flag values with values from config file."""
    projects = []
    for (section, key), value in config_items(args.config_file):
        try:
            if section == "PROJECTS":
                projects.append(value)
                continue
            elif not getattr(args, key) and value:
                setattr(args, key, value)
        except AttributeError:
            raise ConfigurationError(f"Config file key '{key}' is not a valid configuration option.\n")

    if not getattr(args, "project_urls"):
        setattr(args, "project_urls", projects)
    args.neo4j = bool(strtobool(str(args.neo4j)))
    args.quiet = bool(strtobool(str(args.quiet)))
    args.rate_limit = int(args.rate_limit)
    return args


def is_under_configured(args: argparse.Namespace) -> str:
    """Return string of missing keys if there are any."""
    necessary = ["project_urls", "token", "format"]
    neo4j = ["neo4j_user", "neo4j_host", "neo4j_password", "neo4j_boltport"]
    if args.neo4j:
        necessary.extend(neo4j)
    missing = ""
    for key in necessary:
        if not getattr(args, key):
            missing = ", ".join((missing, f"'{key}'"))
    return missing[2:]


def config_items(path: str) -> List[Tuple[Tuple[str, str], Any]]:
    """Return config file option, value pairs."""
    config = configparser.ConfigParser()
    config.read(path)

    res = []
    for section in config.sections():
        for opt, val in config.items(section):
            res.append(((section, opt), val))
    return res


def print_config_summary(args: argparse.Namespace) -> None:
    print("Config summary:", file=sys.stderr)
    for key, val in vars(args).items():
        print(f"{key:14} -> {val}", file=sys.stderr)
