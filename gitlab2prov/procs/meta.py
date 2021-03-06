from __future__ import annotations

import datetime
from typing import Any, Dict, List, NamedTuple, Optional, Type, Union

from prov.constants import PROV_ROLE, PROV_TYPE
from prov.identifier import QualifiedName

from gitlab2prov.utils import p_time, q_name
from gitlab2prov.utils.types import Award, Commit, Issue, Label, MergeRequest, Note


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


class IntermediateRepresentation:
    _prov_type = None
    _node_type = None

    def __init__(self, id_section, attributes, started_at=None, ended_at=None):
        self.id_section = id_section
        self.attributes = attributes
        self.started_at = started_at
        self.ended_at = ended_at

    @property
    def qid(self) -> str:
        if self._node_type is None:
            raise ValueError
        return q_name(f"{self._node_type}-{self.id_section}")

    @property
    def label(self) -> Dict[str, Any]:
        if self._node_type is None:
            raise ValueError

        d = {PROV_TYPE: self._node_type}
        for key, value in self.attributes.items():
            if isinstance(key, QualifiedName):
                d[key] = value
                continue
            d[f"{self._node_type.split('_')[0]}_{key}"] = value
        return d

    def to_prov_element(self) -> Union[Activity, Agent, Entity]:
        if self._prov_type is None:
            raise ValueError

        if self._prov_type is not Activity:
            return self._prov_type(id=self.qid, label=self.label)
        start, end = p_time(self.started_at), p_time(self.ended_at)
        return Activity(id=self.qid, start=start, end=end, label=self.label)


class Creator(IntermediateRepresentation):
    _prov_type = Agent
    _node_type = "user"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_issue(cls, issue: Issue) -> Creator:
        name = issue["author"]["name"]
        attributes = {PROV_ROLE: "creator", "name": name}
        return cls(id_section=name, attributes=attributes)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> Creator:
        """Create a creator meta agent form a merge request API resource."""
        name = merge_request["author"]["name"]
        attributes = {PROV_ROLE: "creator", "name": name}
        return cls(id_section=name, attributes=attributes)


class Author(IntermediateRepresentation):
    _prov_type: Type[Agent] = Agent
    _node_type: str = "user"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_commit(cls, commit: Commit) -> Author:
        """Create an author meta agent from a commit API resource."""
        attr_keys = ["author_name", "author_email"]
        attributes = {key.split("_")[1]: value for key, value in commit.items() if key in attr_keys}
        attributes.update({PROV_ROLE: "author"})
        return cls(id_section=commit["author_name"], attributes=attributes)


class Committer(IntermediateRepresentation):
    _prov_type = Agent
    _node_type = "user"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_commit(cls, commit: Commit) -> Committer:
        """Create an author meta agent from a commit API resource."""
        attr_keys = ["committer_name", "committer_email"]
        attributes = {key.split("_")[1]: value for key, value in commit.items() if key in attr_keys}
        attributes.update({PROV_ROLE: "committer"})
        return cls(id_section=commit["committer_name"], attributes=attributes)


class Initiator(IntermediateRepresentation):
    """MetaAgent representing the initiator of an event."""
    _prov_type = Agent
    _node_type = "user"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_note(cls, note: Note) -> Initiator:
        """Create an initiator meta agent from a note API resource."""
        attributes = {PROV_ROLE: "initiator", "name": note["author"]["name"]}
        return cls(id_section=note["author"]["name"], attributes=attributes)

    @classmethod
    def from_label(cls, label: Label) -> Initiator:
        """Create an initiator meta agent from a label event API resource."""
        attributes = {PROV_ROLE: "initiator", "name": label["user"]["name"]}
        return cls(id_section=label["user"]["name"], attributes=attributes)

    @classmethod
    def from_award(cls, award: Award) -> Initiator:
        """Create an initiator meta agent from an award API resource."""
        attributes = {PROV_ROLE: "initiator", "name": award["user"]["name"]}
        return cls(id_section=award["user"]["name"], attributes=attributes)


class MetaEvent(IntermediateRepresentation):
    _prov_type = Activity
    _node_type = "event"

    initiator = None

    def __init__(self, **kwargs: Any) -> None:
        self.initiator = kwargs["initiator"]
        del kwargs["initiator"]
        super().__init__(**kwargs)

    @classmethod
    def create(cls, initiator: Initiator, created_at: str, attributes: Dict[str, Any]) -> MetaEvent:
        id_section = f"{attributes['event']}-{attributes['event_id']}"
        return cls(
            id_section=id_section,
            started_at=created_at,
            ended_at=created_at,
            attributes=attributes,
            initiator=initiator)


class MetaCommit(IntermediateRepresentation):
    _prov_type = Activity
    _node_type = "commit"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_commit(cls, commit: Commit) -> MetaCommit:
        attr_keys = ["title", "message", "id", "short_id"]
        attributes = {key: value for key, value in commit.items() if key in attr_keys}
        return cls(id_section=commit["id"],
                   started_at=commit["authored_date"],
                   ended_at=commit["committed_date"],
                   attributes=attributes)


class MetaCreation(IntermediateRepresentation):
    _prov_type = Activity
    _node_type = "creation"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_commit(cls, commit: Commit) -> MetaCreation:
        cls._node_type = "commit_creation"
        return cls(id_section=commit["id"],
                   started_at=commit["committed_date"],
                   ended_at=commit["committed_date"],
                   attributes={})

    @classmethod
    def from_issue(cls, issue: Issue) -> MetaCreation:
        cls._node_type = "issue_creation"
        return cls(id_section=issue["id"], started_at=issue["created_at"], ended_at=issue["created_at"], attributes={})

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> MetaCreation:
        cls._node_type = "merge_request_creation"
        return cls(id_section=merge_request["id"],
                   started_at=merge_request["created_at"],
                   ended_at=merge_request["created_at"],
                   attributes={})


class MetaResource(IntermediateRepresentation):
    _prov_type: Type[Entity] = Entity
    _node_type: str = "resource"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_commit(cls, commit: Commit) -> MetaResource:
        cls._node_type = "commit_resource"
        attr_keys = ["title", "message", "short_id", "id"]
        attributes = {key: value for key, value in commit.items() if key in attr_keys}
        return cls(id_section=commit["id"], attributes=attributes)

    @classmethod
    def from_issue(cls, issue: Issue) -> MetaResource:
        cls._node_type = "issue_resource"
        attr_keys = ["id", "iid", "title", "description", "project_id", "web_url"]
        attributes = {key: value for key, value in issue.items() if key in attr_keys}
        return cls(id_section=issue["id"], attributes=attributes)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> MetaResource:
        cls._node_type = "merge_request_resource"
        attr_keys = ["id", "iid", "title", "description", "web_url", "project_id",
                     "source_branch", "target_branch", "source_project_url", "target_project_url"]
        attributes = {key: value for key, value in merge_request.items() if key in attr_keys}
        return cls(id_section=merge_request["id"], attributes=attributes)


class MetaResourceVersion(IntermediateRepresentation):
    _prov_type: Type[Entity] = Entity
    _node_type: str = "resource_version"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def from_commit(cls, commit: Commit, event: Optional[MetaEvent] = None) -> MetaResourceVersion:
        cls._node_type = "commit_resource_version"
        id_section = commit["id"] if event is None else f"{commit['id']}-{event.id_section}"
        return cls(id_section=id_section, attributes={})

    @classmethod
    def from_issue(cls, issue: Issue, event: Optional[MetaEvent] = None) -> MetaResourceVersion:
        cls._node_type = "issue_resource_version"
        id_section = issue["id"] if event is None else f"{issue['id']}-{event.id_section}"
        return cls(id_section=id_section, attributes={})

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest, event: Optional[MetaEvent] = None) -> MetaResourceVersion:
        cls._node_type = "merge_request_resource_version"
        id_section = merge_request["id"] if event is None else f"{merge_request['id']}-{event.id_section}"
        return cls(id_section=id_section, attributes={})

    @classmethod
    def from_meta_versions(cls, version: Entity, event: MetaEvent) -> MetaResourceVersion:
        cls._node_type = f"{version.label[PROV_TYPE]}_version"
        id_section = f"{version.id}-{event.id_section}"
        return cls(id_section=id_section, attributes={})


class File(IntermediateRepresentation):
    _prov_type: Type[Entity] = Entity
    _node_type: str = "file"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def create(cls, path_at_addition: str) -> File:
        return cls(id_section=path_at_addition,
                   attributes={"path_at_addition": "-".join(path_at_addition.split("-")[:-1])})


class FileVersion(IntermediateRepresentation):
    _prov_type: Type[Entity] = Entity
    _node_type: str = "file_version"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def create(cls, path_at_addition: str, old_path: str, new_path: str, sha: str) -> FileVersion:
        attributes = {"old_path": old_path, "new_path": new_path}
        return cls(id_section=f"{path_at_addition}-{sha}", attributes=attributes)


class CommitModelPackage(NamedTuple):
    """Package for commit model implementation."""
    author: Agent
    committer: Agent
    commit: Activity
    parent_commits: List[Activity]
    file_changes: List[Union[Addition, Deletion, Modification]]

    @classmethod
    def from_commit(cls,
                    commit: Commit,
                    parents: List[Commit],
                    diff: List[Union[Addition, Deletion, Modification]]) -> CommitModelPackage:
        a = Author.from_commit(commit).to_prov_element()
        c_agt = Committer.from_commit(commit).to_prov_element()
        c_act = MetaCommit.from_commit(commit).to_prov_element()
        ps = []
        for parent in parents:
            ps.append(MetaCommit.from_commit(parent).to_prov_element())
        return cls(author=a, committer=c_agt, commit=c_act, parent_commits=ps, file_changes=diff)


class CommitCreationPackage(NamedTuple):
    """Represents the creation of a commit resource.

    Subpackage for resource model package."""
    committer: Agent
    commit: Activity
    creation: Activity
    resource: Entity
    resource_version: Entity

    @classmethod
    def from_commit(cls, commit: Commit) -> CommitCreationPackage:
        c_agt = Committer.from_commit(commit).to_prov_element()
        c_act = MetaCommit.from_commit(commit).to_prov_element()
        cr_act = MetaCreation.from_commit(commit).to_prov_element()
        r = MetaResource.from_commit(commit).to_prov_element()
        r_v = MetaResourceVersion.from_commit(commit).to_prov_element()
        return cls(committer=c_agt, commit=c_act, creation=cr_act, resource=r, resource_version=r_v)


class ResourceCreationPackage(NamedTuple):
    """Represents the creation of issue- or merge request resources.

    Subpackage for resource model package."""
    creator: Agent
    creation: Activity
    resource: Entity
    resource_version: Entity

    @classmethod
    def from_issue(cls, issue: Issue) -> ResourceCreationPackage:
        c_agt = Creator.from_issue(issue).to_prov_element()
        c_act = MetaCreation.from_issue(issue).to_prov_element()
        r = MetaResource.from_issue(issue).to_prov_element()
        r_v = MetaResourceVersion.from_issue(issue).to_prov_element()
        return cls(creator=c_agt, creation=c_act, resource=r, resource_version=r_v)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest) -> ResourceCreationPackage:
        c_agt = Creator.from_merge_request(merge_request).to_prov_element()
        c_act = MetaCreation.from_merge_request(merge_request).to_prov_element()
        r = MetaResource.from_merge_request(merge_request).to_prov_element()
        r_v = MetaResourceVersion.from_merge_request(merge_request).to_prov_element()
        return cls(creator=c_agt, creation=c_act, resource=r, resource_version=r_v)


class EventPackage(NamedTuple):
    """Represents an event occurring against a resource.

    Subpackage for resource model package."""
    initiator: Agent
    event: Activity
    resource: Entity
    resource_version: Entity

    @classmethod
    def from_creation(cls, creation: Union[CommitCreationPackage, ResourceCreationPackage]) -> EventPackage:
        i = creation.committer if isinstance(creation, CommitCreationPackage) else creation.creator
        e = creation.commit if isinstance(creation, CommitCreationPackage) else creation.creation
        r = creation.resource
        r_v = creation.resource_version
        return cls(initiator=i, event=e, resource=r, resource_version=r_v)

    @classmethod
    def from_meta_events(cls, latest: MetaEvent, previous: EventPackage) -> EventPackage:
        if latest.initiator is None:
            raise ValueError
        i = latest.initiator.to_prov_element()
        e = latest.to_prov_element()
        r = previous.resource
        r_v = MetaResourceVersion.from_meta_versions(previous.resource, latest).to_prov_element()
        return cls(initiator=i, event=e, resource=r, resource_version=r_v)


class ResourceModelPackage(NamedTuple):
    """Package for resource model implementation."""
    creation: Union[ResourceCreationPackage, CommitCreationPackage]
    event_chain: List[EventPackage]
