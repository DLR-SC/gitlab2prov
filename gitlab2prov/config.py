from __future__ import annotations

import os
import sys
import csv
import logging
import argparse
import configparser
from dataclasses import dataclass, fields
from typing import Optional
from pathlib import Path


logger = logging.getLogger(__name__)


CONFIG: Optional[Configuration] = None
CHECK_CONFIG = "Please check your configuration and try again."


def set_config(entrypoint: str):
    global CONFIG
    if entrypoint == "cli":
        CONFIG = Configuration.from_cli()
    return CONFIG


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
    fmt: str
    pseudonymous: bool
    log: bool
    cprofile: bool
    double_agents: Optional[Path]

    def __post_init__(self):
        if self.fmt not in ["json", "xml", "rdf", "provn", "dot"]:
            raise ValueError(f"Unsupported output format {self.fmt}. {CHECK_CONFIG}")
        if self.double_agents:
            if not os.path.exists(self.double_agents):
                raise FileNotFoundError(
                    "Double agent mapping file {self.double_agents} not found. {CHECK_CONFIG}"
                )
        for field in fields(self):
            logger.info(
                f"SET CONFIG OPTION: {field.name} = {getattr(self, field.name)}"
            )

    @classmethod
    def from_file(cls, fp):
        if not os.path.exists(fp):
            raise FileNotFoundError(f"Could not find config file {fp}. {CHECK_CONFIG}")
        config = configparser.ConfigParser(
            converters={"string": convert_string, "path": convert_path}
        )
        config.read(fp)
        if not config.has_section("GITLAB"):
            raise configparser.NoSectionError(
                f"Missing required config file section [GITLAB]. {CHECK_CONFIG}"
            )
        if not config.has_option("GITLAB", "projects"):
            raise configparser.NoOptionError(
                f"Missing required config file option 'projects'. {CHECK_CONFIG}"
            )
        if not config.has_option("GITLAB", "token"):
            raise configparser.NoOptionError(
                f"Missing required config file option 'token'. {CHECK_CONFIG}"
            )
        return cls(
            parse_csv_str(config.getstring("GITLAB", "projects")),
            config.getstring("GITLAB", "token"),
            config.getstring("OUTPUT", "format", fallback="json"),
            config.getboolean("MISC", "pseudonymous", fallback=False),
            config.getboolean("MISC", "log", fallback=False),
            config.getboolean("MISC", "cprofile", fallback=False),
            config.getpath("MISC", "double_agents", fallback=None),
        )

    @classmethod
    def from_cli(cls):
        parser = argparse.ArgumentParser(
            prog="gitlab2prov",
            description="Extract provenance information from GitLab projects.",
        )
        parser.add_argument(
            "-p",
            "--projects",
            help="gitlab project urls",
            nargs="+",
            metavar="URLS",
            required=not ("--config-file" in sys.argv or "-c" in sys.argv),
        )
        parser.add_argument(
            "-t",
            "--token",
            help="gitlab api access token",
            metavar="TOKEN",
            required=not ("--config-file" in sys.argv or "-c" in sys.argv),
        )
        parser.add_argument(
            "-c", "--config-file", help="config file path", metavar="FILEPATH"
        )
        parser.add_argument(
            "-f",
            "--format",
            help="provenance serialization format",
            choices=["provn", "json", "rdf", "xml", "dot"],
            metavar="STRING",
            default="json",
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
            metavar="FILEPATH",
            default=None,
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
            help="enable logging with log level debug and write the log to 'gl2p.log'",
            action="store_true",
            default=False,
        )
        args = parser.parse_args()
        if args.config_file:
            return cls.from_file(args.config_file)
        return cls(
            args.projects,
            args.token,
            args.format,
            args.pseudonymous,
            args.log,
            args.cprofile,
            args.double_agents,
        )
