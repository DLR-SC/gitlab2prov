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


import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Union, NamedTuple



class PROVNode(NamedTuple):
    """
    Represents a node in a provenance graph.
    """
    id: str
    label: Dict[str, str] = {}


class PROVActivity(NamedTuple):
    """
    Represents an activity node in a provenance graph.
    """
    id: str
    start: datetime.datetime
    end: datetime.datetime
    label: Dict[str, str] = {}


class Addition(NamedTuple):
    """
    Represents a file addition for a commit activity.
    """
    file: PROVNode
    file_v: PROVNode


class Modification(NamedTuple):
    """
    Represents a file modification for a commit activity.
    """
    file: PROVNode
    file_v: PROVNode
    file_v_1: List[PROVNode]


class Deletion(NamedTuple):
    """
    Represents a file deletion for a commit activity.
    """
    file: PROVNode
    file_v: PROVNode


class Commit(NamedTuple):
    """
    Represents a commit.
    """
    author: PROVNode
    committer: PROVNode
    commit: PROVNode
    parents: PROVNode
    files: List[Union[Addition, Modification, Deletion]]


class CommitResourceCreation(NamedTuple):
    """
    Represents the creation of a commit resource.

    Special case of resource creation. 
    Link of commit model and commit resource model.
    """
    committer: PROVNode
    commit: PROVNode
    resource_creation: PROVNode
    resource: PROVNode
    resource_v: PROVNode


class Event(NamedTuple):
    """
    Represents a resource event.
    """
    initiator: PROVNode
    event: PROVNode
    previous_event: PROVNode
    resource: PROVNode
    resource_v: PROVNode
    resource_v_1: PROVNode


class Resource(NamedTuple):
    """
    Represents a resource.
    """
    creation: CommitResourceCreation
    events: List[Event]
