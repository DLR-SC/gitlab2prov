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

import re
from copy import deepcopy
from dataclasses import dataclass, field
from collections.abc import MutableMapping
from typing import List, NamedTuple, Dict
from enum import Enum
from gitlab.v4.objects import ProjectCommit, ProjectIssue


def URLException(Exception):
    pass


def ConfigurationException(Exception):
    pass


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


class RepositoryInfo(NamedTuple):
    path: str
       

class NameTable(MutableMapping):

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return str(self.store)

    def __str__(self):
        return "Nametable: {}".format(self.__repr__())

    def __add__(self, other):
        store = deepcopy(self.store)
        store.update(other)
        return NameTable(store)

    def delta(self, diff):
        # replay changes from diff on a nametable
        store = deepcopy(self.store)
        for entry in diff:
            new, old = entry.get("new_path"), entry.get("old_path")
            if new != old:
                # file moved or renamed
                if old in store:
                    # update existing
                    root = store.get(old)
                    store[new] = root
                else:
                    # update/add
                    store[new] = old
            if entry.get("new_file"):
                store[new] = old
            elif entry.get("deleted_file"):
                pass
            else:
                # modified file
                if new not in store:
                    store[new] = old

        return NameTable(store)             



class CommitEvent:

    def __init__(self, note):
        self.id = note.get("id")
        self.body = note.get("body", "")
        self.initiator = note.get("author").get("name")
        self.reference = None
        self.target = self.conclude_target(note)
        self.date = note.get("created_at")

    def conclude_target(self, note):
        if not note.get("system"):
            return ""
        if "commit" in self.body:
            self.reference = "COMMIT"
            return self.body.split(" ")[-1]
        elif "issue" in self.body:
            self.reference = "ISSUE"
        elif "merge request" in self.body:
            self.reference = "MERGE_REQUEST"
        return re.findall(r'\d+', self.body)[0]

        
@dataclass
class Repository:

    info: RepositoryInfo 
    commits: List
    issues: List
    nametables: Dict[str, NameTable]

    def __str__(self):
        return f"{self.info}\n{self.commits}\n{self.issues}\n{self.nametables}"
