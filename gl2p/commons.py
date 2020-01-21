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
from datetime import datetime
from collections.abc import MutableMapping
from collections import namedtuple
from functools import total_ordering
from typing import List, NamedTuple, Dict, Any
from enum import Enum


class FileStatus(Enum):
    """Action that diff entry represents."""

    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"


@dataclass
class File:
    """A repository file version."""

    old_path: str = ""
    new_path: str = ""
    status: FileStatus = FileStatus.ADDED

    db_id: str = ""
    prev_version_ids: List[str] = ""
    original: str = ""

    @staticmethod
    def _file_status(tup):
        """Determine action occuring for diffed file."""

        new, deleted = tup
        if new:
            return FileStatus.ADDED
        elif deleted:
            return FileStatus.DELETED

        return FileStatus.MODIFIED

    @classmethod
    def from_diff(cls, diff):
        """Create File from diff entry."""

        op, np = diff.get("old_path"), diff.get("new_path")
        nf, df = diff.get("new_file"), diff.get("deleted_file")
        status = cls._file_status((nf, df))

        return cls(op, np, status)
