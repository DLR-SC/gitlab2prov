from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any
from copy import deepcopy

from gitlab2prov.utils.types import Commit, Diff


class FileNameHistory:
    """Compute file name history for each point in the commit tree."""

    def __init__(self) -> None:
        self.history: Dict[str, Dict[str, str]] = dict()
        self.registered_ids: Dict[str, int] = defaultdict(int)

        self.version_history: Dict[str, Dict[str, Set[str]]] = dict()

    def get(self, sha: str, file_name: str) -> str:
        """
        Return name that *file_name* is mapped to in NameTable of commit *sha*.
        """
        return self.history.get(sha, {}).get(file_name, file_name)

    def get_versions(self, sha: str, file_name: str) -> Set[str]:
        """
        Return set of used versions for a file in a certain commit.
        """
        return self.version_history.get(sha, {}).get(file_name, set())

    @classmethod
    def compute(cls, commits: List[Commit], diffs: List[Diff]) -> FileNameHistory:
        obj = cls()
        tree, orphans = obj.commit_tree(commits), obj.orphans(commits)
        commit_lookup, diff_lookup = obj.lookups(commits, diffs)
        obj.compute_file_name_history(tree, orphans, commit_lookup, diff_lookup)
        obj.compute_file_version_history(tree, orphans, commit_lookup, diff_lookup)
        return obj

    def compute_file_name_history(self,
                                  tree: Dict[str, Set[str]],
                                  orphans: List[str],
                                  commits: Dict[str, Commit],
                                  diffs: Dict[str, Diff]) -> None:
        """
        Compute FileNameHistory from list of commits and list of diffs.
        """
        queue = deque(orphans)
        while queue:
            sha = queue.popleft()
            commit, diff = commits[sha], diffs[sha]

            if self.parents_cached(commit, self.history):
                if sha in self.history:
                    continue
                if not commit["parent_ids"]:
                    # Commit without parents (orphan)
                    # Apply diff to empty dictionary
                    self.history[sha] = self.apply_diff(diff, {})
                else:
                    parent_mappings = [self.history[parent_sha] for parent_sha in commit["parent_ids"]]
                    acc = {}
                    for mapping in parent_mappings:
                        acc.update(self.apply_diff(diff, mapping))
                    self.history[sha] = acc

                queue.extend(tree.get(sha, []))
            else:
                queue.append(sha)

    def apply_diff(self, diff: Diff, mapping: Dict[str, str]) -> Dict[str, str]:
        """
        Apply diff entries to a file name mapping.
        """
        ret_mapping = deepcopy(mapping)
        for entry in diff:
            old, new = entry["old_path"], entry["new_path"]
            if new != old:  # renamed
                if old in ret_mapping:
                    ret_mapping[new] = ret_mapping[old]
                    continue
                ret_mapping[new] = old
            elif entry["new_file"]:  # added
                # check whether this path has been used before,
                # if so update the max id for the path
                max_n = self.registered_ids[new]
                original_id = f"{new}-{max_n+1 if max_n > 0 else 0}"
                self.registered_ids[new] += 1
                ret_mapping[new] = original_id
        return ret_mapping

    def compute_file_version_history(self,
                                     tree: Dict[str, Set[str]],
                                     orphans: List[str],
                                     commit_lookup: Dict[str, Commit],
                                     diff_lookup: Dict[str, Diff]) -> None:
        """
        Compute file version history.
        """
        queue = deque(orphans)
        while queue:
            sha = queue.popleft()
            commit = commit_lookup[sha]
            if self.parents_cached(commit, self.version_history):
                if sha in self.version_history:
                    continue
                if not commit["parent_ids"]:
                    # default for commit without parents (orphan)
                    self.version_history[sha] = {}
                else:
                    mappings = []
                    for parent_id in commit["parent_ids"]:
                        parent_diff = diff_lookup[parent_id]
                        parent_mapping = self.version_history[parent_id]
                        mappings.append(self.apply_version_diff(parent_id, parent_diff, parent_mapping))

                    unified = deepcopy(mappings[0])
                    for mapping in mappings[1:]:
                        for file_id, versions in mapping.items():
                            if file_id not in unified:
                                unified[file_id] = versions
                            else:
                                unified[file_id].update(versions)
                    self.version_history[sha] = unified

                queue.extend(tree.get(sha, []))
            else:
                queue.append(sha)

    def apply_version_diff(self,
                           parent_id: str,
                           parent_diff: Diff,
                           parent_mapping: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """
        Apply a diff to a file version mapping.
        """
        ret_mapping = deepcopy(parent_mapping)
        for entry in parent_diff:
            new, old = entry["new_path"], entry["old_path"]
            origin = self.history[parent_id][new]
            if entry["new_file"] or new != old:
                ret_mapping[origin] = {parent_id}
            elif entry["deleted_file"]:
                ret_mapping[origin] = set()
            elif new == old and not entry["new_file"] and not entry["deleted_file"]:
                ret_mapping[origin] = {parent_id}
        return ret_mapping

    @staticmethod
    def parents_cached(commit: Commit, history: Dict[str, Any]) -> bool:
        """
        Return whether all parents of *commit* have an entry in self.history.
        """
        ps = commit["parent_ids"]
        return all(p in history for p in ps)

    @staticmethod
    def lookups(commits: List[Commit], diffs: List[Diff]) -> Tuple[Dict[str, Commit], Dict[str, Diff]]:
        """
        Return mapping of commit ids to commits and commit ids to diffs.
        """
        if len(commits) != len(diffs):
            raise ValueError(f"Unequal amount of diffs and commits.")
        cl, dl = {}, {}
        for commit, diff in zip(commits, diffs):
            cl[commit["id"]] = commit
            dl[commit["id"]] = diff
        return cl, dl

    @staticmethod
    def commit_tree(commits: List[Commit]) -> Dict[str, Set[str]]:
        """
        Return commit tree build from commits.

        Tree represented as mapping of commit id's to set's of children
        commit id's.
        """
        tree: Dict[str, Set[str]] = defaultdict(set)
        for commit in commits:
            for p_id in commit["parent_ids"]:
                tree[p_id].add(commit["id"])
        return tree

    @staticmethod
    def orphans(commits: List[Commit]) -> List[str]:
        """
        Return list of commits that do not have parents.
        """
        return [c["id"] for c in commits if not c["parent_ids"]]
