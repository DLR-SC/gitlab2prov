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

from dataclasses import dataclass, field, asdict
import datetime
from typing import NamedTuple, Union, Dict, List, Any, Iterable, Tuple
from gl2p.utils.types import Note, Label, Award


class Candidates(NamedTuple):
    labels: List[Label]
    awards: List[Award]
    notes: List[Note]
    note_awards: List[Award]


@dataclass
class ParseableContainer:
    """
    Container for event candidates.
    """
    labels: List[List[Label]] = field(default_factory=list)
    awards: List[List[Award]] = field(default_factory=list)
    notes: List[List[Note]] = field(default_factory=list)
    note_awards: List[List[Award]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Match all attribute values to same length.
        """
        selfdict = asdict(self)
        max_len = len(max(selfdict.values(), key=len))

        if not max_len:
            return

        for key, value in selfdict.items():
            if len(value):
                # don't override items
                continue
            # fill up to max len with empty lists
            value = [list() for _ in range(max_len)]
            setattr(self, key, value)

    def __iter__(self) -> Iterable[Tuple[List[Label], List[Award], List[Note], List[Award]]]:
        """
        Return iterator over stored attributes.
        """
        for zipped in zip(self.labels, self.awards, self.notes, self.note_awards):
            yield Candidates(*zipped)


@dataclass
class GL2PEvent:
    """
    Internal event representation.
    """
    id: str = ""
    initiator: str = ""
    created_at: str = ""
    label: Dict[str, Any] = field(default_factory=dict)


class Activity(NamedTuple):
    """
    Represent a PROV activity.
    """
    id: str
    start: datetime.datetime
    end: datetime.datetime
    label: Dict[str, str]


class Agent(NamedTuple):
    """
    Represent a PROV agent.
    """
    id: str
    label: Dict[str, str]


class Entity(NamedTuple):
    """
    Represent a PROV entity.
    """
    id: str
    label: Dict[str, str]


class Addition(NamedTuple):
    """
    Represent the addition of a new file.
    """
    file: Entity
    file_v: Entity


class Modification(NamedTuple):
    """
    Represent the modification of a file.
    """
    file: Entity
    file_v: Entity
    file_v_1: List[Entity]


class Deletion(NamedTuple):
    """
    Represent the deletion of a file.
    """
    file: Entity
    file_v: Entity


# PROV-DM Groupings
class CommitResource(NamedTuple):
    """
    Represent a git commit.
    """
    author: Agent
    committer: Agent
    commit: Activity
    parents: List[Activity]
    changes: List[Union[Addition, Deletion, Modification]]


class Creation(NamedTuple):
    """
    Represent the creation of a resource.
    """
    creator: Agent
    creation: Activity
    resource: Entity
    resource_version: Entity


class CommitCreation(NamedTuple):
    """
    Represent the creation of a commit resource. Special case of Creation.
    """
    committer: Agent
    commit: Activity
    creation: Activity
    resource: Entity
    resource_version: Entity


class Event(NamedTuple):
    """
    Represent an event occuring on a resource.
    """
    initiator: Agent
    event: Activity
    previous_event: Activity
    resource: Entity
    resource_version: Entity
    previous_resource_version: Entity


class Resource(NamedTuple):
    """
    Represent the lifecycle of a resource. From it's creation,
    to a list of events occuring on the resource.
    """
    creation: Union[Creation, CommitCreation]
    events: List[Event]
