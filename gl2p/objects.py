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


from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, NamedTuple
import datetime

from gl2p.helpers import qname


@dataclass
class PROVNode:
    """
    A node ready to insert into a prov document.
    """
    
    identifier: str
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """
        Convert string identifier to uuid5 representation.
        """
        self.identifier = qname(str(self.identifier))

@dataclass
class PROVActivity(PROVNode):

    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None


@dataclass
class Addition:

    file: PROVNode
    file_v: PROVNode


@dataclass
class Modification:

    file: PROVNode
    file_v: PROVNode
    file_v_1: List[PROVNode]


@dataclass
class Deletion:

    file: PROVNode
    file_v: PROVNode


@dataclass
class Commit:

    author: PROVNode
    parent_commits: PROVNode
    committer: PROVNode
    commit: PROVNode
    files: List[Union[Addition, Modification, Deletion]]

@dataclass
class CommitResourceCreation:
    """
    Container for everything commit resource creation related.

    Special case of resource creation. 
    Linkage of commit model and commit resource model.
    """

    committer: PROVNode
    commit: PROVNode
    resource_creation: PROVNode
    resource: PROVNode
    resource_v: PROVNode


@dataclass
class Event:
    """
    A resource event.
    """

    initiator: PROVNode
    event: PROVNode
    previous_event: PROVNode
    resource: PROVNode
    resource_v: PROVNode
    resource_v_1: PROVNode


@dataclass
class Resource:
    """
    A resource.
    """

    creation: CommitResourceCreation
    events: List[Event]
