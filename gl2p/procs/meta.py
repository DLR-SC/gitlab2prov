from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from typing import (Any, Deque, Dict, Iterator, List, NamedTuple, Optional,
                    Union)

from prov.constants import PROV_ROLE, PROV_TYPE

from ..utils import ptime, qname
from ..utils.types import Award, Commit, Issue, Label, MergeRequest, Note


class Agent(NamedTuple):
    """W3C PROV atom representing an agent."""
    id: str
    label: Dict[str, Any]


class Activity(NamedTuple):
    """W3C PROV atom representing an activity."""
    id: str
    start: datetime.datetime
    end: datetime.datetime
    label: Dict[str, Any]


class Entity(NamedTuple):
    """W3C PROV atom representing an entity."""
    id: str
    label: Dict[str, Any]


class Addition(NamedTuple):
    """File change package representing the addition of a new file."""
    file: Entity
    file_v: Entity


class Modification(NamedTuple):
    """File change package representing the modification of an existing file."""
    file: Entity
    file_v: Entity
    file_v_1: List[Entity]


class Deletion(NamedTuple):
    """File change package representing the deletion of an existing file."""
    file: Entity
    file_v: Entity


@dataclass
class MetaAgent:
    """
    Meta object implementing the conversion of an API Resource to a PROV agent.

    Provides conversion interface for subclasses by .qid and .label properties.
    Connection between the API layer and the atom layer.
    """
    role: str
    name: str
    email: Optional[str] = None
    denominator: str = "user"

    @property
    def qid(self) -> str:
        """
        The project unique id of the represented meta agent.

        The ID is the string representation of the uuid5 digest of
        uuid.NAMESPACE_DNS and a provided string consisting of
        the denominator and name of the meta agent.
        """
        return qname(f"{self.denominator}-{self.name}")

    @property
    def label(self) -> Dict[str, Any]:
        """
        The label of the represented meta agent.

        The label consists of information about the agent,
        including their name and email address if available.
        """
        label = {
            PROV_TYPE: self.denominator,
            PROV_ROLE: self.role,
            "name": self.name
        }
        if not self.email:
            return label

        label.update({"email": self.email})
        return label

    def atomize(self) -> Agent:
        """
        Return package ready PROV agent representation of the meta agent.

        Marks the connection between the meta and the atom layer.
        """
        return Agent(self.qid, self.label)


@dataclass
class Creator(MetaAgent):
    """
    MetaAgent representing the creator of a collaborative resource,
    such as an issue or a merge request.
    """
    @classmethod
    def from_issue(cls, issue: Issue) -> Creator:
        """
        Create a creator meta agent from an issue API resource.
        """
        role = "creator"
        name = issue["author"]["name"]
        return cls(role, name)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> Creator:
        """
        Create a creator meta agent form a merge request API resource.
        """
        role = "creator"
        name = merge_request["author"]["name"]
        return cls(role, name)


@dataclass
class Author(MetaAgent):
    """
    MetaAgent representing the author of a commit.
    """
    @classmethod
    def from_commit(cls, commit: Commit) -> Author:
        """
        Create an author meta agent from a commit API resource.
        """
        role = "author"
        name = commit["author_name"]
        email = commit["author_email"]
        return cls(role, name, email)


@dataclass
class Committer(MetaAgent):
    """
    MetaAgent representing the committer of a commit.
    """
    @classmethod
    def from_commit(cls, commit: Commit) -> Committer:
        """
        Create a committer meta agent from a commit API resource.
        """
        role = "committer"
        name = commit["committer_name"]
        email = commit["committer_email"]
        return cls(role, name, email)


@dataclass
class Initiator(MetaAgent):
    """
    MetaAgent representing the initiator of an event.
    """
    @classmethod
    def from_note(cls, note: Note) -> Initiator:
        """
        Create an initiator meta agent from a note API resource.
        """
        role = "initiator"
        name = note["author"]["name"]
        return cls(role, name)

    @classmethod
    def from_label_event(cls, label_event: Label) -> Initiator:
        """
        Create an initiator meta agent from a label event API resource.
        """
        role = "initiator"
        name = label_event["user"]["name"]
        return cls(role, name)

    @classmethod
    def from_award_emoji(cls, award: Award) -> Initiator:
        """
        Create an initiator meta agent from an award (emoji) API resource.
        """
        role = "initiator"
        name = award["user"]["name"]
        return cls(role, name)


@dataclass
class MetaActivity:
    """
    Meta object implementing an interface for
    conversion of API Resources to PROV activities.

    Provides conversion interface for subclasses by qid, start, end and label properties.
    Connection between the API layer and the atom layer.
    """
    denominator: str
    identifier: str
    start_str: str
    end_str: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def qid(self) -> str:
        """
        The project unique id string of the represented meta activity.

        The ID is the string representation of the uuid5 digest of
        uuid.NAMESPACE_DNS and a provided string consisting of
        the denominator and identifier of the meta activity.
        """
        return qname(f"{self.denominator}-{self.identifier}")

    @property
    def start(self) -> datetime.datetime:
        """
        The start date of the represented meta activity.
        """
        return ptime(self.start_str)

    @property
    def end(self) -> datetime.datetime:
        """
        The end date of the represented meta activity.
        """
        return ptime(self.end_str)

    @property
    def label(self) -> Dict[str, Any]:
        """
        The label dictionary of the represented meta activity.

        The label consists of information about the activity,
        which varies across different activity types.
        """
        return {PROV_TYPE: self.denominator, **self.details}

    def atomize(self) -> Activity:
        """
        Return package ready PROV activity from the meta agent.

        Marks the connection between the meta and the atom layer.
        """
        return Activity(self.qid, self.start, self.end, self.label)


@dataclass
class MetaEvent(MetaActivity):
    """
    MetaActivity representing an event occuring against a collaborativ resource.

    Provides a meta agent that acts as the initiator of the wrapped event.
    Return type of the event parser.
    """
    initiator: Initiator = Initiator("", "")  # simple dummy on init

    @classmethod
    def create(cls, initiator: Initiator, created_at: str, label: Dict[str, Any]) -> MetaEvent:
        """
        Create meta event from parsed event data.

        Used by the event paser as an object constructor.
        We define events to occur instantaneously, thus
        the event start date is also the event end date.
        """
        identifier = f"{label['event']}-{label['event_id']}"  # id creation as placeholder before uri usage.
        return cls("event", identifier, created_at, created_at, label, initiator)


@dataclass
class MetaCommit(MetaActivity):
    """
    MetaActivity representing a commit for the commit model.
    """
    @classmethod
    def from_commit(cls, commit: Commit) -> MetaCommit:
        """
        Create meta commit from commit API resource.
        """
        details = {
            "title": commit["title"],
            "message": commit["message"],
            "sha": commit["id"],
            "short_sha": commit["short_id"]
        }
        return cls(
            "commit",
            commit["id"],
            commit["authored_date"],
            commit["committed_date"],
            details
        )


@dataclass
class MetaCreation(MetaActivity):
    """
    MetaActivity representing the creation of a collaborative resource.
    """
    @classmethod
    def from_commit(cls, commit: Commit) -> MetaCreation:
        """
        Create a meta creation from a commit API resource.
        """
        return cls(
            "commit_creation",
            commit["id"],
            commit["committed_date"],
            commit["committed_date"]
        )

    @classmethod
    def from_issue(cls, issue: Issue) -> MetaCreation:
        """
        Create a meta creation from an issue API resource.
        """
        return cls("issue_creation", issue["id"], issue["created_at"], issue["created_at"])

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> MetaCreation:
        """
        Create a meta creation from a merge request API resource.
        """
        return cls(
            "merge_request_creation",
            merge_request["id"],
            merge_request["created_at"],
            merge_request["created_at"]
        )


@dataclass
class MetaEntity:
    """
    Meta object implementing an interface for
    conversion of API Resources to PROV entities.

    Provides interface for subclasses by implementing qid and label properties.
    Connection between the API layer and the atom layer.
    """
    denominator: str
    identifier: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def qid(self) -> str:
        """
        The project unique identifier of the represented entity.

        The ID is the string representation of the uuid5 digest of
        uuid.NAMESPACE_DNS and a provided string consisting of
        the denominator and identifier of the meta entity.
        """
        return qname(f"{self.denominator}-{self.identifier}")

    @property
    def label(self) -> Dict[str, Any]:
        """
        The label of the represented meta entity.

        The label consists of information about the represented enitiy,
        which varies across different entity types.
        """
        return {PROV_TYPE: self.denominator, **self.details}

    def atomize(self) -> Entity:
        """
        Return package ready PROV entity of the meta entity.

        Marks the connection between the meta and the atom layer.
        """
        return Entity(self.qid, self.label)


@dataclass
class MetaResource(MetaEntity):
    """
    MetaEntity representing a collaborativ resource.

    Collaborativ resources can be issues, merge requests or
    in fact the comment section of a commit.
    """
    @classmethod
    def from_commit(cls, commit: Commit) -> MetaResource:
        """
        Create meta resource from commit API resource.
        """
        details = {
            "title": commit["title"],
            "message": commit["message"],
            "sha": commit["id"],
            "short_sha": commit["short_id"],
            #"web_url": commit["web_url"]
        }
        return cls("commit_resource", commit["id"], details)

    @classmethod
    def from_issue(cls, issue: Issue) -> MetaResource:
        """
        Create meta resource from issue API resource.
        """
        details = {
            "id": issue["id"],
            "iid": issue["iid"],
            "title": issue["title"],
            "description": issue["description"],
            "project_id": issue["project_id"],
            "web_url": issue["web_url"]
        }
        return cls("issue_resource", issue["id"], details)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> MetaResource:
        """
        Create meta resource from merge request API resource.
        """
        details = {
            "id": merge_request["id"],
            "iid": merge_request["iid"],
            "title": merge_request["title"],
            "description": merge_request["description"],
            "web_url": merge_request["web_url"],
            "project_id": merge_request["project_id"],
            "source_branch": merge_request["source_branch"],
            "target_branch": merge_request["target_branch"],
            "source_project_id": merge_request["source_project_id"],
            "target_project_id": merge_request["target_project_id"],
        }
        return cls("merge_request_resource", merge_request["id"], details)


@dataclass
class MetaResourceVersion(MetaResource):
    """
    MetaEntity representing a version of a meta resource.
    """
    @classmethod
    def create(cls, sp: MetaResource, add: Optional[MetaEvent] = None) -> MetaResourceVersion:
        """
        Create meta resource version from a meta resource and an optional meta event.
        """
        deno = f"{sp.denominator}_version"
        iden = sp.identifier
        if add:
            iden = f"{iden}-{add.identifier}"
        return cls(deno, iden)

    @classmethod
    def from_commit(cls, commit: Commit, add: Optional[MetaEvent] = None) -> MetaResourceVersion:
        """
        Create a meta resource version from a commit API resource and an optional meta event.
        """
        sp = super().from_commit(commit)
        return cls.create(sp, add)

    @classmethod
    def from_issue(cls, issue: Issue, add: Optional[MetaEvent] = None) -> MetaResourceVersion:
        """
        Create a meta resource version from a issue API resource and an optional meta event.
        """
        sp = super().from_issue(issue)
        return cls.create(sp, add)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest, add: Optional[MetaEvent] = None) -> MetaResourceVersion:
        """
        Create a meta resource version from a merge request API resource and an optional meta event.
        """
        sp = super().from_merge_request(merge_request)
        return cls.create(sp, add)


@dataclass
class File(MetaEntity):
    """
    MetaEntity representing a file in the commit model.
    """
    @classmethod
    def create(cls, origin: str) -> File:
        """
        Create file from the its original name at point of addition.
        """
        return cls("file", origin, {"original_path": origin})


@dataclass
class FileVersion(MetaEntity):
    """
    MetaEntity representing a version of a file in the commit model.
    """
    @classmethod
    def create(cls, origin: str, old_path: str, new_path: str, sha: str) -> FileVersion:
        """
        Create file version from multiple parts computed in the change set computation.
        """
        details = {"old_path": old_path, "new_path": new_path}
        return cls("file_version", f"{origin}-{sha}", details)


class CommitModelPackage(NamedTuple):
    """
    Package for commit model implementation.
    """
    author: Agent
    committer: Agent
    commit: Activity
    parent_commits: List[Activity]
    file_changes: List[Union[Addition, Deletion, Modification]]


class CommitCreationPackage(NamedTuple):
    """
    Represents the creation of a commit resource.

    Subpackage for resource model package.
    """
    committer: Agent
    commit: Activity
    creation: Activity
    resource: Entity
    resource_version: Entity


class CreationPackage(NamedTuple):
    """
    Represents the creation of issue- or merge request resources.

    Subpackage for resource model package.
    """
    creator: Agent
    creation: Activity
    resource: Entity
    resource_version: Entity


class EventPackage(NamedTuple):
    """
    Represents an event occuring against a resource.

    Subpackage for resource model package.
    """
    initiator: Agent
    event: Activity
    resource: Entity
    resource_version: Entity


class ResourceModelPackage(NamedTuple):
    """
    Package for resource model implementation.
    """
    creation: Union[CreationPackage, CommitCreationPackage]
    event_chain: Deque[EventPackage]


class Candidates(NamedTuple):
    """
    Simple container for resources that denote events.

    Used as a bundle for event parsing.
    """
    labels: List[Label]
    awards: List[Award]
    notes: List[Note]
    note_awards: List[Award]


@dataclass
class ParseableContainer:
    """
    Container for multiple lists of resources that denote events.
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

    def __iter__(self) -> Iterator[Candidates]:
        """
        Return iterator over stored attributes.
        """
        for zipped in zip(self.labels, self.awards, self.notes, self.note_awards):
            yield Candidates(*zipped)
