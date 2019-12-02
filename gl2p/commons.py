# Evaluate for Issue Model

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
