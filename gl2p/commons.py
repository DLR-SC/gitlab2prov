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
from dataclasses import dataclass
from typing import List, NamedTuple
from enum import Enum
# third party imports
# local imports


class Actor(NamedTuple):
    name: str
    email: str


class Time(NamedTuple):
    committed: str
    authored: str


class FileStatus(Enum):
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"


@dataclass
class File:
    commit_sha: str
    old_path: str
    new_path: str
    status: FileStatus

    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return (self.commit_sha, self.old_path, self.new_path) == (self.commit_sha, other.old_path, other.new_path)

    def __hash__(self):
        return hash((self.old_path, self.new_path))


@dataclass
class Commit:
    sha: str
    msg: str
    time: Time
    author: Actor
    committer: Actor
    parents: List[str] # list of parent shas
    files: List[File] # list of files touched in diff


@dataclass
class Container:

    def __init__(self, commits:List[Commit]):
        
        # init
        self._commits = dict()
        self.files = list()
        
        # fill
        for commit in commits:
            self._commits[commit.sha] = commit
        self.files = self._extract_files()

    def __repr__(self):
        return "Container([Commit()])"

    def __str__(self):
        return "COMMITS --» {} \n\nFILES --» {} \n\nISSUES --» None".format(self.commits, self.files)

    def _extract_files(self):
        if not self._commits: 
            return list()
        files = list()
        for commit in self._commits.values():
            for f in commit.files:
                files.append(f)
        return files

    def commits(self):
        return self._commits.values()

    def get_commit(self, sha):
        return self._commits.get(sha, None)

    def get_files(self, sha):
        if sha in self._commits:
            return self.commits[sha].files


def URLException(Exception):
    pass


def ConfigurationException(Exception):
    pass
