from __future__ import annotations

import abc
from datetime import datetime
from dataclasses import dataclass, field, fields
from typing import Optional, Any, TypeAlias
from urllib.parse import urlencode

from prov.identifier import QualifiedName

from gitlab2prov.domain.constants import ProvType
from gitlab2prov.prov.operations import qualified_name


SKIP = {
    "SKIP": "This field should not be included in the prov attributes of a dataclass."
}



Attributes: TypeAlias = list[tuple[str, Any]]


def prov_attributes(dataclass: BaseHooks) -> Attributes:
    attrs: Attributes = [(PROV_LABEL, dataclass.prov_label)]
    for field in fields(dataclass):
        if field.metadata == SKIP:
            continue
        name = PROV_FIELDS.get(field.name, field.name)
        if field.type == "list[str]":
            attrs.extend((name, val) for val in getattr(dataclass, field.name))
        else:
            attrs.append((name, getattr(dataclass, field.name)))
    return attrs


@dataclass
class BaseHooks(abc.ABC):
    @property
    def prov_identifier(self) -> QualifiedName:
        attrs = {f.name: getattr(self, f.name) for f in fields(self) if f.repr}
        query = urlencode(attrs)
        return qualified_name(f"{type(self).__name__}?{query}")

    @property
    def prov_attributes(self) -> Attributes:
        return prov_attributes(self)

    @property
    def prov_label(self) -> QualifiedName:
        return qualified_name(repr(self))

    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError


@dataclass
class EntityHooks(BaseHooks):
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_attributes


@dataclass
class ActivityHooks(BaseHooks):
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_start
        yield self.prov_end
        yield self.prov_attributes


@dataclass
class AgentHooks(BaseHooks):
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_attributes


@dataclass(unsafe_hash=True)
class User(AgentHooks):
    name: str
    email: Optional[str] = field(default=None)
    gitlab_username: Optional[str] = field(default=None, repr=False)
    gitlab_id: Optional[str] = field(default=None, repr=False)
    prov_role: str = field(repr=False, default="")
    prov_type: str = field(init=False, repr=False, default=ProvType.User)

    def __post_init__(self):
        self.email = self.email.lower() if self.email else None


@dataclass(unsafe_hash=True)
class File(EntityHooks):
    path: str
    commit_hexsha: str
    prov_type: str = field(init=False, repr=False, default=ProvType.File)


@dataclass(unsafe_hash=True)
class FileRevision(EntityHooks):
    path: str
    commit_hexsha: str
    change_type: str
    original: File = field(repr=False, metadata=SKIP)
    previous: Optional[FileRevision] = field(repr=False, default=None, metadata=SKIP)
    prov_type: str = field(init=False, repr=False, default=ProvType.FileRevision)


@dataclass(unsafe_hash=True)
class GitCommit(ActivityHooks):
    hexsha: str
    message: str = field(repr=False)
    title: str = field(repr=False)
    author: User = field(repr=False, metadata=SKIP)
    committer: User = field(repr=False, metadata=SKIP)
    parents: list[str] = field(repr=False, metadata=SKIP)
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: str = field(init=False, repr=False, default=ProvType.GitCommit)


@dataclass(unsafe_hash=True)
class Annotation(ActivityHooks):
    id: str
    type: str
    body: str = field(repr=False)
    annotator: User = field(repr=False, metadata=SKIP)
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    kwargs: dict[str, Any] = field(repr=False, default_factory=dict, metadata=SKIP)
    prov_type: str = field(init=False, repr=False, default=ProvType.Annotation)

    @property
    def prov_attributes(self):
        attributes = prov_attributes(self)
        attributes.extend(self.kwargs.items())
        return attributes


@dataclass(unsafe_hash=True)
class Issue(EntityHooks):
    id: str
    iid: str
    title: str
    description: str = field(repr=False)
    url: str = field(repr=False)
    author: User = field(repr=False, metadata=SKIP)
    annotations: list[Annotation] = field(repr=False, metadata=SKIP)
    created_at: datetime = field(repr=False)
    closed_at: Optional[datetime] = field(repr=False, default=None)
    prov_type: str = field(init=False, repr=False, default=ProvType.Issue)

    @property
    def creation(self) -> Creation:
        return Creation(
            self.id, self.created_at, self.closed_at, ProvType.IssueCreation
        )

    @property
    def first_version(self) -> Version:
        return Version(self.id, ProvType.IssueVersion)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion(self.id, annotation.id, ProvType.AnnotatedIssueVersion)
            for annotation in self.annotations
        ]


@dataclass(unsafe_hash=True)
class GitlabCommit(EntityHooks):
    hexsha: str
    url: str
    author: User = field(repr=False, metadata=SKIP)
    annotations: list[Annotation] = field(repr=False, metadata=SKIP)
    authored_at: datetime = field(repr=False)
    committed_at: datetime = field(repr=False)
    prov_type: str = field(init=False, repr=False, default=ProvType.GitlabCommit)

    @property
    def creation(self) -> Creation:
        return Creation(
            self.hexsha,
            self.authored_at,
            self.committed_at,
            ProvType.GitlabCommitCreation,
        )

    @property
    def first_version(self) -> Version:
        return Version(self.hexsha, ProvType.GitlabCommitVersion)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion(
                self.hexsha, annotation.id, ProvType.AnnotatedGitlabCommitVersion
            )
            for annotation in self.annotations
        ]


@dataclass(unsafe_hash=True)
class MergeRequest(EntityHooks):
    id: str
    iid: str
    title: str
    description: str = field(repr=False)
    url: str = field(repr=False)
    source_branch: str = field(repr=False)
    target_branch: str = field(repr=False)
    author: User = field(repr=False, metadata=SKIP)
    annotations: list[Annotation] = field(repr=False, metadata=SKIP)
    created_at: datetime = field(repr=False)
    closed_at: Optional[datetime] = field(repr=False, default=None)
    merged_at: Optional[datetime] = field(repr=False, default=None)
    first_deployed_to_production_at: Optional[datetime] = field(
        repr=False, default=None
    )
    prov_type: str = field(init=False, repr=False, default=ProvType.MergeRequest)

    @property
    def creation(self) -> Creation:
        return Creation(
            self.id, self.created_at, self.closed_at, ProvType.MergeRequestCreation
        )

    @property
    def first_version(self) -> Version:
        return Version(self.id, ProvType.MergeRequestVersion)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion(
                self.id, annotation.id, ProvType.AnnotatedMergeRequestVersion
            )
            for annotation in self.annotations
        ]


@dataclass(unsafe_hash=True)
class Version(EntityHooks):
    version_id: str
    prov_type: str = field(repr=False)

    @property
    def prov_identifier(self):
        attrs = {f.name: getattr(self, f.name) for f in fields(self) if f.repr}
        query = urlencode(attrs)
        return qualified_name(f"{self.prov_type}?{query}")

    @property
    def prov_label(self):
        cls_name = self.prov_type
        attributes = [f"{f.name}={getattr(self, f.name)}" for f in fields(self)]
        label = f"{cls_name}({', '.join(attributes)})"
        return qualified_name(label)


@dataclass(unsafe_hash=True)
class AnnotatedVersion(EntityHooks):
    version_id: str
    annotation_id: str
    prov_type: str = field(repr=False)

    @property
    def prov_identifier(self):
        attrs = {f.name: getattr(self, f.name) for f in fields(self) if f.repr}
        query = urlencode(attrs)
        return qualified_name(f"{self.prov_type}?{query}")

    @property
    def prov_label(self):
        cls_name = self.prov_type
        attributes = [f"{f.name}={getattr(self, f.name)}" for f in fields(self)]
        label = f"{cls_name}({', '.join(attributes)})"
        return qualified_name(label)


@dataclass(unsafe_hash=True)
class Tag(EntityHooks):
    name: str
    hexsha: str
    message: Optional[str] = field(repr=False)
    author: User = field(repr=False, metadata=SKIP)
    created_at: datetime = field(repr=False)
    prov_type: list[str] = field(
        init=False,
        repr=False,
        default_factory=lambda: [ProvType.Tag, ProvType.Collection],
    )

    @property
    def creation(self) -> Creation:
        return Creation(
            self.name, self.created_at, self.created_at, ProvType.TagCreation
        )


@dataclass(unsafe_hash=True)
class Asset(EntityHooks):
    url: str
    format: str
    prov_type: str = field(init=False, repr=False, default=ProvType.Asset)


@dataclass(unsafe_hash=True)
class Evidence(EntityHooks):
    hexsha: str
    url: str
    collected_at: datetime
    prov_type: str = field(init=False, repr=False, default=ProvType.Evidence)


@dataclass(unsafe_hash=True)
class Release(EntityHooks):
    name: str
    description: str = field(repr=False)
    tag_name: str = field(repr=False)
    author: Optional[User] = field(repr=False, metadata=SKIP)
    assets: list[Asset] = field(repr=False, metadata=SKIP)
    evidences: list[Evidence] = field(repr=False, metadata=SKIP)
    created_at: datetime = field(repr=False)
    released_at: datetime = field(repr=False)
    prov_type: list[str] = field(
        init=False,
        repr=False,
        default_factory=lambda: [ProvType.Release, ProvType.Collection],
    )

    @property
    def creation(self) -> Creation:
        return Creation(
            self.name, self.created_at, self.released_at, ProvType.ReleaseCreation
        )


@dataclass(unsafe_hash=True)
class Creation(ActivityHooks):
    creation_id: str
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: str = field(repr=False)

    @property
    def prov_identifier(self):
        attrs = {f.name: getattr(self, f.name) for f in fields(self) if f.repr}
        query = urlencode(attrs)
        return qualified_name(f"{self.prov_type}?{query}")

    @property
    def prov_label(self):
        cls_name = self.prov_type
        attributes = [f"{f.name}={getattr(self, f.name)}" for f in fields(self)]
        label = f"{cls_name}({', '.join(attributes)})"
        return qualified_name(label)
