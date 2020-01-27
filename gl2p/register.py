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


from __future__ import annotations

from collections import UserDict, defaultdict, deque
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from functools import reduce
from typing import Any, Dict, Generator, Iterator, List, Optional, Set


@dataclass
class FileNameRegister:
    """
    Track of file naming changes.

    Builds a mappings of file names tot their original names for each commit in the commit tree.
    """

    commits: Union[Dict[str, Any], List[Any]]
    diffs: Union[Dict[str, Any], List[Any]]

    __register: Dict[str, NameTable] = field(default_factory=dict)

    def __post_init__(self):
        """
        Transform class arguments into mappings and compute the register.
        """
        cs = {commit.get("id"): commit for commit in self.commits}
        dfs = {
            commit.get("id"): diff for commit, diff in zip(self.commits, self.diffs)
        }

        self.commits = cs
        self.diffs = dfs
        self.__register = self.compute_nametables()

    def get(self, sha: str, file_name: str) -> str:
        """
        Given a file name and a commit sha, return the original 
        name of the file according to the computed mapping of commit sha.

        Returns:
            str: The original file name of *file_name* if found else file_name
        """

        if sha in self.__register:
            nt = self.__register.get(sha, NameTable())
            name = nt.get(file_name, file_name)

            return name

        return file_name

    def compute_nametables(self):
        # TODO: better description of what actually happens here.
        """
        Compute mapping for each point in the commit tree.
        
        Walk commit tree by BFS.
        """
        
        tree = self.commit_tree()
        queue = deque(self.orphans())

        register = {}

        while queue:
            sha = queue.popleft()
            diff = self.diffs.get(sha)
            commit = self.commits.get(sha)

            if sha in register:
                continue

            if all(self.parents_cached(commit, register)):
                parents = commit.get("parent_ids")

                if not parents:
                    register[sha] = NameTable.from_diff(diff)
                else:
                    nts = [register.get(parent) for parent in parents]
                    nts = [nt.apply(diff) for nt in nts]
                    register[sha] = reduce(NameTable.merge, nts)

                queue.extend(tree.get(sha, []))
            else:
                queue.append(sha)

        return register

    def commit_tree(self) -> Dict[str, Set[str]]:
        """
        Compute the commit tree stemming from self.commits.

        The tree is represented by a mapping of commit sha's
        to sets of children sha's.

        Returns:
            Dict[str, set]: Mapping from commit sha's to sets of children sha's.
        """

        tree = defaultdict(set)  # type: Dict[str, Set]

        for commit in self.commits.values():
            commit, parents = commit.get("id"), commit.get("parent_ids", [])

            for parent in parents:
                tree[parent].add(commit)

        return tree

    def orphans(self) -> Iterator[str]:
        """
        Generator for commits that don't have parents.
        
        Yields:
            str: The sha of a commit
        """

        for commit in self.commits.values():
            if not commit.get("parent_ids"):
                yield commit.get("id")

    def parents_cached(self, commit: Dict[str, Any], register: Dict[str, Any]) -> Iterator[bool]:
        """
        Generator yielding whether parents of commit have a cached nametable.

        Parameters:
            commit: Commit for which to check whether parents have a nametable.
        Yields: 
            bool: Whether parent has an entry in nametable cache.
        """

        for parent in commit.get("parent_ids", []):
            yield (parent in register)


class NameTable(UserDict):
    """
    A mapping of file names to their original names for a single commit.
    
    Generate NameTable for commit x by applying diff of x to NameTable of commit x-1.
    """

    @staticmethod
    def merge(nt1: NameTable, nt2: NameTable) -> NameTable:
        """
        Merge two nametables nt1, nt2.

        Returns:
            NameTable: A name table containing all entries 
             from nt1 updated with entries from nt2.
        """

        copy = deepcopy(nt1.data)
        copy.update(nt2.data)

        return NameTable(copy)

    @classmethod
    def from_diff(cls, diff) -> NameTable:
        """
        Instantiate an empty NameTable and apply diff to it.
        """

        return cls().apply(diff)

    def apply(self, diff: List[Dict[str:Any]]) -> NameTable:
        """
        Apply a diff to the current NameTable.
        """

        copy = deepcopy(self.data)
        for entry in diff:
            new, old = entry.get("new_path"), entry.get("old_path")

            if entry.get("new_file"):
                copy[new] = old

            if new != old:
                root = copy.get(old)
                if not root:
                    continue
                copy[new] = root

            if new not in copy:
                copy[new] = old

        return NameTable(copy)
