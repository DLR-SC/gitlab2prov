import sys
import csv
import argparse
import configparser
from dataclasses import dataclass
from typing import Optional


SUPPORTED_FORMATS = ["json", "rdf", "xml", "provn", "dot"]


@dataclass
class Config:
    project_urls: list[str]
    token: str
    format: str
    pseudonymous: bool
    verbose: bool
    profile: bool
    double_agents: Optional[str]


def convert_string(s: str) -> str:
    return s.strip("'").strip('"')


def convert_csv(csv_string: str) -> list[str]:
    lines = csv_string.splitlines()
    reader = csv.reader(lines)
    [urls] = list(reader)
    urls = [url.strip().strip("'").strip('"') for url in urls]
    return urls


def read_file(config_file: str) -> Config:
    config = configparser.ConfigParser(
        converters={"string": convert_string, "csv": convert_csv}
    )
    config.read(config_file)
    return Config(
        config.getcsv("GITLAB", "project_urls"),
        config.getstring("GITLAB", "token"),
        config.getstring("OUTPUT", "format", fallback="json"),
        config.getboolean("MISC", "pseudonymous", fallback=False),
        config.getboolean("MISC", "verbose", fallback=False),
        config.getboolean("MISC", "profile", fallback=False),
        config.getstring("MISC", "double_agents", fallback=None),
    )


def read_cli() -> Config:
    parser = argparse.ArgumentParser(
        prog="gitlab2prov",
        description="Extract provenance information from GitLab projects.",
    )
    parser.add_argument(
        "-p",
        "--project-urls",
        help="gitlab project urls",
        nargs="+",
        required="--config-file" not in sys.argv and "-c" not in sys.argv,
    )
    parser.add_argument(
        "-t",
        "--token",
        help="gitlab api access token",
        required="--config-file" not in sys.argv and "-c" not in sys.argv,
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
    args = parser.parse_args()
    if args.config_file:
        return read_file(args.config_file)
    return Config(
        args.project_urls,
        args.token,
        args.format,
        args.pseudonymous,
        args.verbose,
        args.profile,
        args.double_agents,
    )
