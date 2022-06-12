import sys
import csv
import argparse
import configparser
from dataclasses import dataclass
from typing import Optional, Tuple, Union


SUPPORTED_FORMATS = ["json", "rdf", "xml", "provn", "dot"]


@dataclass
class Config:
    project_urls: list[str]
    token: str
    format: Union[str, list[str]]
    outfile: Optional[str]
    pseudonymous: bool
    verbose: bool
    profile: bool
    double_agents: Optional[str]


class ConfigError(Exception):
    pass


def convert_string(s: str) -> str:
    return s.strip("'").strip('"')


def convert_csv(csv_string: str) -> list[str]:
    lines = csv_string.splitlines()
    reader = csv.reader(lines)
    [items] = list(reader)
    items = [item.strip().strip("'").strip('"') for item in items]
    return items


def check_mode_requirements(config: configparser.ConfigParser) -> Tuple[bool, str]:
    if len(config.getstring("OUTPUT", "format")) > 1:
        if "outfile" not in config["OUTPUT"]:
            return False, "Missing option 'outfile' in section 'OUTPUT'"
        if config.getstring("OUTPUT", "outfile") is None:
            return False, "Missing value for option 'outfile' in section 'OUTPUT'"
    return True, ""


def read_config():
    conf, file = read_cli()
    if file:
        conf = read_file(file)
    if conf is None:
        return None
    return conf


def read_file(config_file: str) -> Config:
    config = configparser.ConfigParser(
        converters={"string": convert_string, "csv": convert_csv}
    )
    config.read(config_file)

    ok, msg = check_mode_requirements(config)
    if not ok:
        raise ConfigError(msg)

    return Config(
        config.getcsv("GITLAB", "project_urls"),
        config.getstring("GITLAB", "token"),
        config.getcsv("OUTPUT", "format", fallback=["json"]),
        config.getstring("OUTPUT", "outfile", fallback=None),
        config.getboolean("MISC", "pseudonymous", fallback=False),
        config.getboolean("MISC", "verbose", fallback=False),
        config.getboolean("MISC", "profile", fallback=False),
        config.getstring("MISC", "double_agents", fallback=None),
    )


def token_required(argv):
    if not argv[1:]:
        return False
    if "-c" in argv or "--config-file" in argv:
        return False
    return True


def read_cli() -> tuple[Optional[Config], Optional[str]]:
    parser = argparse.ArgumentParser(
        prog="gitlab2prov",
        description="Extract provenance information from GitLab projects.",
    )

    subparsers = parser.add_subparsers(help="")
    multiformat = subparsers.add_parser(
        "multi-format", help="serialize output in multiple formats"
    )
    multiformat.add_argument(
        "-f",
        "--format",
        help="provenance serialization formats",
        nargs="+",
        choices=SUPPORTED_FORMATS,
        default=["json"],
    )
    multiformat.add_argument(
        "-o",
        "--outfile",
        help="serialize to {outfile}.{format} for each specified format",
        required=True,
    )

    parser.add_argument(
        "-p",
        "--project-urls",
        help="gitlab project urls",
        nargs="+",
        required=token_required(sys.argv),
    )
    parser.add_argument(
        "-t",
        "--token",
        help="gitlab api access token",
        required=token_required(sys.argv),
    )
    parser.add_argument("-c", "--config-file", help="config file path")
    parser.add_argument(
        "-f",
        "--format",
        help="provenance serialization format",
        choices=SUPPORTED_FORMATS,
        default="json",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="write log to stderr, set log level to DEBUG",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--double-agents",
        help="agent mapping file path",
        default=None,
    )
    parser.add_argument(
        "--pseudonymous",
        help="pseudonymize user names by enumeration",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--profile",
        help="enable deterministic profiling, write profile to 'gitlab2prov-run-$TIMESTAMP.profile' where $TIMESTAMP is the current timestamp in 'YYYY-MM-DD-hh-mm-ss' format",
        action="store_true",
        default=False,
    )

    if not sys.argv[1:]:
        print(parser.format_help())
        return None, None

    args = parser.parse_args()
    if args.config_file:
        return None, args.config_file

    return (
        Config(
            args.project_urls,
            args.token,
            args.format,
            args.pseudonymous,
            args.verbose,
            args.profile,
            args.double_agents,
        ),
        None,
    )
