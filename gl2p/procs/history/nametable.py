from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict

from gl2p.utils.types import Diff


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
