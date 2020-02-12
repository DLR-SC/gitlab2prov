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


APIResource = Dict[str, Any]


@dataclass
class EventCandidates:

    labels: List[APIResource] = field(default_factory=list)
    awards: List[APIResource] = field(default_factory=list)
    notes: List[APIResource] = field(default_factory=list)
    note_awards: List[APIResource] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Fill all class properties to same length.

        Default value is an empty dict.
        """
        max_len = len(max(asdict(self).values(), key=len))

        if not self.labels:
            self.labels = [{} for _ in range(max_len)]

        if not self.awards:
            self.awards = [{} for _ in range(max_len)]

        if not self.notes:
            self.notes = [{} for _ in range(max_len)]

        if not self.note_awards:
            self.note_awards = [{} for _ in range(max_len)]


@dataclass
class EventCandidateContainer:
    """
    A container for API resources that represent gl2p resource events.
    """
    labels: List[List[APIResource]] = field(default_factory=list)
    awards: List[List[APIResource]] = field(default_factory=list)
    notes: List[List[APIResource]] = field(default_factory=list)
    note_awards: List[List[APIResource]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Fill all class properties to same length.

        Default value is an empty list.
        """
        max_len = len(max(asdict(self).values(), key=len))

        if not self.labels:
            self.labels = [[] for _ in range(max_len)]

        if not self.awards:
            self.awards = [[] for _ in range(max_len)]

        if not self.notes:
            self.notes = [[] for _ in range(max_len)]

        if not self.note_awards:
            self.note_awards = [[] for _ in range(max_len)]

    def zip(self, iterable: Iterable[APIResource]) -> Iterable[Tuple[APIResource, EventCandidates]]:
        """
        Yield items from iterable zipped with items from container.
        """
        for item, *candidates in zip(iterable, self.labels, self.awards, self.notes, self.note_awards):
            yield item, EventCandidates(*candidates)


@dataclass
class GL2PEvent:
    """
    Internal event representation.
    """
    id: str
    initiator: str
    label: Dict[str, Any]
    created_at: str


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
