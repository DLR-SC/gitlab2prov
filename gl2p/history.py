"""Compute the file name history from the commit tree."""


from __future__ import annotations

import collections
from copy import deepcopy
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field


Diff = List[Dict[str, Any]]
Commit = Dict[str, Any]


@dataclass
class FileNameHistory:
    """Compute file name history for each point in the commit tree."""
    history: Dict[str, NameTable] = field(default_factory=dict)

    def get(self, sha: str, file_name: str) -> str:
        """
        Return name that *file_name* is mapped to in NameTable of commit *sha*.
        """
        return self.history.get(sha, NameTable()).get(file_name, file_name)

    def compute(self, commits: List[Commit], diffs: List[Diff]) -> None:
        """
        Create NameTables for each commit by walking the commit tree.

        TODO: Description
        """
        clookup, dlookup = self.lookups(commits, diffs)
        tree = self.commit_tree(commits)
        orphans = self.orphans(commits)

        q = collections.deque(orphans)

        while q:
            sha = q.popleft()
            diff = dlookup[sha]
            commit = clookup[sha]

            if self.parents_cached(commit):
                # skip if commit already has a computed NameTable
                if sha in self.history:
                    continue

                parents = commit["parent_ids"]

                if not parents:
                    # init value
                    # empty NameTable with diff applied
                    self.history[sha] = NameTable.from_diff(diff)
                else:
                    # NameTables of parent commits to current commit
                    nts = [self.history[parent] for parent in parents]

                    # accumulator NameTable
                    acc = nts[0].apply(diff)  # type: NameTable

                    for nt in nts[1:]:
                        # apply diff to NameTable before merging
                        nt = nt.apply(diff)
                        # merge into accumulator
                        acc = acc.merge(nt)

                    # store for current commit
                    self.history[sha] = acc

                # enqueue children of current commit
                q.extend(tree.get(sha, []))
            else:
                # wait in queue iff parenting NameTables haven't been computed
                q.append(sha)

    def parents_cached(self, commit: Commit) -> bool:
        """
        Return whether all parents of *commit* have an entry in self.history.
        """
        ps = commit["parent_ids"]
        return all(p in self.history for p in ps)

    def lookups(self, commits: List[Commit], diffs: List[Diff]) -> Tuple[Dict[str, Commit], Dict[str, Diff]]:
        """
        Return mapping of commit ids to commits and commit ids to diffs.
        """
        if len(commits) != len(diffs):
            raise ValueError(
                f"{len(commits)} Commits. {len(diffs)} Diffs.\
                Expected same amount of Commits and Diffs."
            )

        cl, dl = {}, {}

        for c, d in zip(commits, diffs):
            cl[c["id"]] = c
            dl[c["id"]] = d

        return cl, dl

    def commit_tree(self, commits: List[Commit]) -> Dict[str, Set[str]]:
        """
        Return commit tree build from commits.

        Tree represented as mapping of commit id's to set's of children
        commit id's.
        """
        tree = collections.defaultdict(set)  # type: Dict[str, Set[str]]

        for c in commits:
            c_id = c["id"]  # type: str
            parent_ids = c["parent_ids"]  # type: str

            for p_id in parent_ids:
                tree[p_id].add(c_id)

        return tree

    def orphans(self, commits: List[Commit]) -> List[str]:
        """Return list of commits that do not have parents."""
        return [c["id"] for c in commits if not c["parent_ids"]]


@dataclass
class NameTable:
    """
    A mapping of filenames to the names that they had when they got added.
    Suffices for just one commit n.
    """

    data: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_diff(cls, diff: Diff) -> NameTable:
        """
        Return NameTable instance created from *diff*.

        Create an empty NameTable and apply *diff* to it.
        """
        return cls().apply(diff)

    def get(self, name: str, default: str = "") -> str:
        """
        Return NameTable entry for key name.

        Return default if key is not in self.data.
        """
        return self.data.get(name, default)

    def merge(self, other: NameTable) -> NameTable:
        """
        Return NameTable resulting from merge of *self* with *other*.

        Merge two NameTable's (*self* and *other*) by updating the
        entries of *self* with the entries of *other*.
        """
        if not isinstance(other, NameTable):
            raise TypeError(f"Expected type NameTable, got {type(other)}")

        copy = deepcopy(self.data)
        copy.update(other.data)

        return NameTable(copy)

    def apply(self, diff: Diff) -> NameTable:
        """
        Return copy of *self* with diff applied.

        We can compute the NameTable NT of commit n+1 given *diff* and
        *self* as follows:

        for each entry ...
            ... let NT be a copy of NameTable *self*
            ... let NEW be the new file path of f
            ... let OLD be the old file path of f

            ,if
                ... entry denotes that f has been added,
                    - add NT entry NEW -> OLD

                ... NEW != OLD and OLD has an entry in NT,
                    - add NT entry NEW -> NT[OLD]

                ... NEW still not in NT,
                    - add NT entry NEW -> OLD
        """
        copy = deepcopy(self.data)

        for entry in diff:
            new = entry["new_path"]  # type: str
            old = entry["old_path"]  # type: str

            if entry["new_file"]:
                copy[new] = old

            if new != old and old in copy:
                copy[new] = copy[old]

            if new not in copy:
                copy[new] = old

        return NameTable(copy)
