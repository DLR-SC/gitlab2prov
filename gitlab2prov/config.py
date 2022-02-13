import os
import sys
import csv
import logging
import argparse
import configparser
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    pass


def parse_csv_str(s: str):
    reader = csv.reader([s])
    unqoute = lambda s: convert_string(s)
    parsed = [unqoute(f) for fields in reader for f in fields if f]
    return parsed


def convert_string(s: str):
    return s.strip("'").strip('"')


def convert_path(fp: str):
    if fp is None:
        return None
    if fp in ["", '""', "''"]:
        return None
    return Path(fp)


@dataclass
class Configuration:
    projects: list[str]
    token: str
    fmt: str = "json"
    pseudonymous: bool = False
    log: bool = False
    cprofile: bool = False
    double_agents: Optional[Path] = None
    config_file: Optional[Path] = None

    @staticmethod
    def validate_config_file(parser, filepath):
        try:
            parser["GITLAB"]
        except configparser.NoSectionError:
            raise ConfigurationError(
                f"Config file {filepath} is missing the required section [GITLAB].\n"
                f"Please check your config file and try again."
            )

        try:
            parser["GITLAB"]["projects"]
        except configparser.NoOptionError:
            raise ConfigurationError(
                f"Config file {filepath} is missing the required option 'projects'.\n"
                f"gitlab2prov doesn't know which projects to mine, when no urls are specified.\n"
                f"Please check your config file and try again."
            )

        try:
            s = parser["GITLAB"]["projects"]
            parse_csv_str(s)
        except Exception:
            raise ConfigurationError(
                f"Could not parse a list of urls from {s}.\n"
                f"Values for the config option 'projects' have to be seperated by commas (aka. csv).\n"
                f"Please check your config file and try again."
            )

        try:
            parser.getstring("GITLAB", "token")
        except configparser.NoOptionError:
            raise ConfigurationError(
                f"Config file {filepath} is missing the required option 'token'.\n"
                f"Without a token, gitlab2prov can't perform authenticated API request.\n"
                f"Please check your config file and try again."
            )

        fmt = parser.getstring("OUTPUT", "format", fallback="json")
        if fmt not in ["json", "rdf", "xml", "provn", "dot"]:
            raise Warning(
                f"Format {fmt} is not a supported output format.\n"
                f"Using the fallback format 'json', gitlab2prov will continue.",
                file=sys.stderr,
            )

        filepath = parser.getpath("MISC", "double_agents", fallback=None)
        if filepath is not None:
            if not os.path.exists(filepath):
                raise Warning(
                    f"Specified double agent mapping {filepath} could not be found.\n"
                    f"Please check the specified file path in your config file.\n"
                    f"gitlab2prov will continue without a mapping.",
                )

    @staticmethod
    def validate_cli_args(args):
        if args.config_file:
            return
        if not args.projects:
            raise ConfigurationError(
                "Gitlab project urls are required but where not provided. Please check your command line configuration and try again."
            )
        if not args.token:
            raise ConfigurationError(
                "Gitlab access token is required but was not provided. Please check your command line configuration and try again."
            )

    @classmethod
    def from_file(cls, filepath):
        parser = configparser.ConfigParser(
            converters={"string": convert_string, "path": convert_path}
        )
        parser.read(filepath)
        try:
            cls.validate_config_file(parser, filepath)
        except Warning as msg:
            logger.warning(msg.replace("\n", " "))
        except Exception as exeption:
            raise exeption
        return cls(
            parse_csv_str(parser["GITLAB"]["projects"]),
            parser.getstring("GITLAB", "token"),
            parser.getstring("OUTPUT", "format"),
            parser.getboolean("MISC", "pseudonymous", fallback=False),
            parser.getboolean("MISC", "log", fallback=False),
            parser.getboolean("MISC", "cprofile", fallback=False),
            parser.getpath("MISC", "double_agents", fallback=None),
            parser.getpath("MISC", "config_file", fallback=None),
        )

    @classmethod
    def from_cli(cls):
        parser = argparse.ArgumentParser(
            prog="gitlab2prov",
            description="Extract provenance information from GitLab projects.",
        )
        parser.add_argument("-p", "--projects", help="gitlab project urls", nargs="+", metavar="URLS")
        parser.add_argument("-t", "--token", help="gitlab api access token", metavar="TOKEN")
        parser.add_argument("-c", "--config-file", help="config file path", metavar="FILEPATH")
        parser.add_argument(
            "-f",
            "--format",
            help="provenance serialization format",
            choices=["provn", "json", "rdf", "xml", "dot"],
            default="json",
            metavar="STRING"
        )
        parser.add_argument(
            "--double-agents",
            help=(
                "Filepath to a file that contains equivalence classes for user names (agents). "
                "A single user can have multiple names across his local git config and gitlab account. "
                "The generated provenance graph can therefore contain multiple PROV agents that all represent the same user. "
                "To merge these 'double agents' into one, you can provide a mapping in .json format. "
                "More information about the mapping format can be found at 'https://github.com/dlr-sc/gitlab2prov'."
            ),
            metavar="FILEPATH"
        )
        parser.add_argument(
            "--pseudonymous",
            help="pseudonymize user names by enumeration",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--cprofile",
            help="enable runtime profiling and store stats in 'gl2p.stats'",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--log",
            help="enable logging, set the log level to debug and write log to 'gl2p.log'",
            action="store_true",
            default=False,
        )
        args = parser.parse_args()
        try:
            cls.validate_cli_args(args)
        except Exception as exception:
            raise exception
        return cls(
            args.projects,
            args.token,
            args.format,
            args.pseudonymous,
            args.log,
            args.cprofile,
            args.double_agents,
            args.config_file,
        )


config: Optional[Configuration] = None
config = Configuration.from_cli()
if config.config_file:
    config = Configuration.from_file(config.config_file)
