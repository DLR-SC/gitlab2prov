import argparse
import configparser
import os
import sys
from distutils.util import strtobool
from typing import Any, List, Tuple


prog = "gitlab2prov"
description = "Extract provenance information from GitLab projects."


class ConfigurationError(Exception):
    pass


def get_config() -> argparse.Namespace:
    """Return configuration namespace."""
    parser = get_parser()
    args = parser.parse_args()
    if args.config_file:
        if os.path.exists(args.config_file):
            args = patch(args)

    if is_under_configured(args):
        missing_options = is_under_configured(args)
        parser.print_help()
        raise ConfigurationError(f"\nMissing values for config options: {missing_options}")

    return args

def get_parser() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog, None, description)

    parser.add_argument("-p", "--project-urls",
                       help="gitlab project urls", nargs="+", metavar="<string>")
    parser.add_argument("-t", "--token",
                       help="gitlab api access token", metavar="<string>")
    parser.add_argument("-r", "--rate-limit",
                       help="api client rate limit (in req/s)", metavar="<int>", type=int)
    parser.add_argument("-c", "--config-file",
                       help="config file path", metavar="<string>")
    parser.add_argument("-f", "--format",
                       help="provenance output format", choices=["provn", "json", "rdf", "xml", "dot"])
    parser.add_argument("-q", "--quiet",
                       help="suppress output to stdout", action="store_true")
    parser.add_argument("--aliases", metavar="<string>",
                       help="path to agent alias mapping json file")
    parser.add_argument("--pseudonymize", action="store_true",
                       help="pseudonymize agents")
    return parser


def patch(args: argparse.Namespace) -> argparse.Namespace:
    """Try to patch missing flag values with values from config file."""
    if not args.config_file:
        return args

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
    args.quiet = bool(strtobool(str(args.quiet)))
    args.rate_limit = int(args.rate_limit)
    return args


def is_under_configured(args: argparse.Namespace) -> str:
    """Return string of missing keys if there are any."""
    necessary = ["project_urls", "token", "format"]
    missing = ""
    for key in necessary:
        if not getattr(args, key):
            missing = ", ".join((missing, f"'--{key}'"))
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
