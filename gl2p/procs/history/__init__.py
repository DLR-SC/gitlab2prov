from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from gl2p.utils.types import Commit, Diff

from .nametable import NameTable


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

        q = deque(orphans)

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
        tree = defaultdict(set)  # type: Dict[str, Set[str]]

        for c in commits:
            c_id = c["id"]  # type: str
            parent_ids = c["parent_ids"]  # type: str

            for p_id in parent_ids:
                tree[p_id].add(c_id)

        return tree

    def orphans(self, commits: List[Commit]) -> List[str]:
        """Return list of commits that do not have parents."""
        return [c["id"] for c in commits if not c["parent_ids"]]
