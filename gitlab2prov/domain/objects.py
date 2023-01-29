from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from prov.model import (
    PROV_LABEL,
    PROV_ROLE,
    ProvDocument,
    ProvAgent,
    ProvActivity,
    ProvEntity,
    PROV_TYPE,
    PROV_ATTR_STARTTIME,
    PROV_ATTR_ENDTIME,
)
from prov.identifier import QualifiedName

from gitlab2prov.domain.constants import ProvType
from gitlab2prov.prov.operations import qualified_name


PLACEHOLDER = ProvDocument()
PLACEHOLDER.set_default_namespace("http://github.com/dlr-sc/gitlab2prov/")


@dataclass
class User:
    name: str
    email: str
    gitlab_username: str | None = None
    github_username: str | None = None
    gitlab_id: str | None = None
    github_id: str | None = None
    prov_role: str | None = None

    def __post_init__(self):
        self.email = self.email.lower() if self.email else None

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"User?{self.name=}&{self.email=}")

    def to_prov_element(self) -> ProvAgent:
        attributes = [
            ("name", self.name),
            ("email", self.email),
            (PROV_ROLE, self.prov_role),
            (PROV_TYPE, ProvType.USER),
        ]
        if self.gitlab_username:
            attributes.append(("gitlab_username", self.gitlab_username))
        if self.github_username:
            attributes.append(("github_username", self.github_username))
        if self.gitlab_id:
            attributes.append(("gitlab_id", self.gitlab_id))
        if self.github_id:
            attributes.append(("github_id", self.github_id))
        return ProvAgent(PLACEHOLDER, self.identifier, attributes)


@dataclass
class File:
    name: str
    path: str
    commit: str

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"File?{self.name=}&{self.path=}&{self.commit=}")

    def to_prov_element(self) -> ProvEntity:
        attributes = [("name", self.name), ("path", self.path), (PROV_TYPE, ProvType.FILE)]
        return ProvEntity(
            PLACEHOLDER,
            self.identifier,
            attributes,
        )


@dataclass
class FileRevision(File):
    status: str
    file: File | None = None
    previous: FileRevision | None = None

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(
            f"FileRevision?{self.name=}&{self.path=}&{self.commit=}&{self.status=}"
        )

    def to_prov_element(self) -> ProvEntity:
        attributes = [
            ("name", self.name),
            ("path", self.path),
            ("status", self.status),
            (PROV_TYPE, ProvType.FILE_REVISION),
        ]
        return ProvEntity(
            PLACEHOLDER,
            self.identifier,
            attributes,
        )


@dataclass
class Annotation:
    uid: str
    name: str
    body: str
    start: datetime
    end: datetime
    annotator: User
    captured_kwargs: dict[str, Any] = field(default_factory=dict)

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Annotation?{self.uid=}&{self.name=}")

    def to_prov_element(self) -> ProvActivity:
        attributes = [
            ("uid", self.uid),
            ("name", self.name),
            ("body", self.body),
            (PROV_ATTR_STARTTIME, self.start),
            (PROV_ATTR_ENDTIME, self.end),
            (PROV_TYPE, ProvType.ANNOTATION),
            *(("captured_" + k, v) for k, v in self.captured_kwargs.items()),
        ]
        return ProvActivity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class Version:
    uid: str
    resource: str

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"{self.resource}Version?{self.uid=}")

    @classmethod
    def from_commit(cls, commit: Commit):
        return cls(uid=commit.sha, resource=ProvType.COMMIT)

    @classmethod
    def from_issue(cls, issue: Issue):
        return cls(uid=issue.id, resource=ProvType.ISSUE)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest):
        return cls(uid=merge_request.id, resource=ProvType.MERGE_REQUEST)

    def to_prov_element(self) -> ProvEntity:
        attributes = [("uid", self.uid), (PROV_TYPE, f"{self.resource}Version")]
        return ProvEntity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class AnnotatedVersion:
    uid: str
    aid: str
    resource: str
    start: datetime

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Annotated{self.resource}Version?{self.uid=}&{self.aid=}")

    @classmethod
    def from_commit(cls, commit: Commit, annotation: Annotation):
        return cls(uid=commit.sha, aid=annotation.uid, resource=ProvType.COMMIT, start=annotation.start)

    @classmethod
    def from_issue(cls, issue: Issue, annotation: Annotation):
        return cls(uid=issue.id, aid=annotation.uid, resource=ProvType.ISSUE, start=annotation.start)

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest, annotation: Annotation):
        return cls(uid=merge_request.id, aid=annotation.uid, resource=ProvType.MERGE_REQUEST, start=annotation.start)

    def to_prov_element(self) -> ProvEntity:
        attributes = [("uid", self.uid), (PROV_TYPE, f"Annotated{self.resource}Version")]
        return ProvEntity(
            PLACEHOLDER,
            self.identifier,
            attributes,
        )


@dataclass
class Creation:
    uid: str
    resource: str
    start: datetime
    end: datetime

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Creation?{self.uid=}&{self.resource=}")

    @classmethod
    def from_tag(cls, tag: GitTag):
        return cls(uid=tag.name, resource=ProvType.TAG, start=tag.created_at, end=tag.created_at)

    @classmethod
    def from_commit(cls, commit: Commit):
        return cls(
            uid=commit.sha,
            resource=ProvType.COMMIT,
            start=commit.authored_at,
            end=commit.committed_at,
        )

    @classmethod
    def from_issue(cls, issue: Issue):
        return cls(
            uid=issue.id, resource=ProvType.ISSUE, start=issue.created_at, end=issue.closed_at
        )

    @classmethod
    def from_merge_request(cls, merge_request: MergeRequest):
        return cls(
            uid=merge_request.id,
            resource=ProvType.MERGE_REQUEST,
            start=merge_request.created_at,
            end=merge_request.closed_at,
        )

    def to_prov_element(self) -> ProvActivity:
        attributes = [
            ("uid", self.uid),
            (PROV_ATTR_STARTTIME, self.start),
            (PROV_ATTR_ENDTIME, self.end),
            (PROV_TYPE, ProvType.CREATION),
        ]
        return ProvActivity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class GitCommit:
    sha: str
    title: str
    message: str
    author: User
    committer: User
    parents: list[str]
    start: datetime  # authored date
    end: datetime  # committed date

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"GitCommit?{self.sha=}")

    def to_prov_element(self) -> ProvActivity:
        attributes = [
            ("sha", self.sha),
            ("title", self.title),
            ("message", self.message),
            ("authored_at", self.start),
            ("committed_at", self.end),
            (PROV_ATTR_STARTTIME, self.start),
            (PROV_ATTR_ENDTIME, self.end),
            (PROV_TYPE, ProvType.GIT_COMMIT),
        ]
        return ProvActivity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class Issue:
    id: str
    iid: str
    platform: str
    title: str
    body: str
    url: str
    author: User
    annotations: list[Annotation]
    created_at: datetime = field(repr=False)
    closed_at: datetime | None = field(repr=False, default=None)

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Issue?{self.id=}")

    @property
    def creation(self) -> Creation:
        return Creation.from_issue(self)

    @property
    def first_version(self) -> Version:
        return Version.from_issue(self)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [AnnotatedVersion.from_issue(self, annotation) for annotation in self.annotations]

    def to_prov_element(self) -> ProvActivity:
        attributes = [
            ("id", self.id),
            ("iid", self.iid),
            ("platform", self.platform),
            ("title", self.title),
            ("body", self.body),
            ("url", self.url),
            ("platform", self.platform),
            (PROV_ATTR_STARTTIME, self.created_at),
            (PROV_ATTR_ENDTIME, self.closed_at),
            (PROV_TYPE, ProvType.ISSUE),
        ]
        return ProvActivity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class Commit:
    sha: str
    url: str
    author: User
    platform: str
    annotations: list[Annotation]
    authored_at: datetime
    committed_at: datetime

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Commit?{self.sha=}")

    @property
    def creation(self) -> Creation:
        return Creation.from_commit(self)

    @property
    def first_version(self) -> Version:
        return Version.from_commit(self)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [AnnotatedVersion.from_commit(self, annotation) for annotation in self.annotations]

    def to_prov_element(self) -> ProvActivity:
        attributes = [
            ("sha", self.sha),
            ("url", self.url),
            ("platform", self.platform),
            (PROV_ATTR_STARTTIME, self.authored_at),
            (PROV_ATTR_ENDTIME, self.committed_at),
            (PROV_TYPE, ProvType.COMMIT),
        ]
        return ProvActivity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class MergeRequest:
    id: str
    iid: str
    title: str
    body: str
    url: str
    platform: str
    source_branch: str  # base for github
    target_branch: str  # head for github
    author: User
    annotations: list[Annotation]
    created_at: datetime
    closed_at: datetime | None = None
    merged_at: datetime | None = None
    first_deployed_to_production_at: datetime | None = None

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"MergeRequest?{self.id=}")

    @property
    def creation(self) -> Creation:
        return Creation.from_merge_request(self)

    @property
    def first_version(self) -> Version:
        return Version.from_merge_request(self)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion.from_merge_request(self, annotation)
            for annotation in self.annotations
        ]

    def to_prov_element(self) -> ProvActivity:
        attributes = [
            ("id", self.id),
            ("iid", self.iid),
            ("title", self.title),
            ("body", self.body),
            ("url", self.url),
            ("platform", self.platform),
            ("source_branch", self.source_branch),
            ("target_branch", self.target_branch),
            (PROV_ATTR_STARTTIME, self.created_at),
            (PROV_ATTR_ENDTIME, self.closed_at),
            (PROV_TYPE, ProvType.MERGE_REQUEST),
        ]
        return ProvActivity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class GitTag:
    name: str
    sha: str
    message: str | None
    author: User
    created_at: datetime

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"GitTag?{self.name=}")

    @property
    def creation(self) -> Creation:
        return Creation.from_tag(self)

    def to_prov_element(self) -> ProvEntity:
        attributes = [
            ("name", self.name),
            ("sha", self.sha),
            ("message", self.message),
            (PROV_ATTR_STARTTIME, self.created_at),
            (PROV_ATTR_ENDTIME, self.created_at),
            (PROV_TYPE, ProvType.TAG),
            (PROV_TYPE, ProvType.COLLECTION),
        ]
        return ProvEntity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class Asset:
    url: str
    format: str

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Asset?{self.url=}")

    def to_prov_element(self) -> ProvEntity:
        attributes = [
            ("url", self.url),
            ("format", self.format),
            (PROV_TYPE, ProvType.ASSET),
        ]
        return ProvEntity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class Evidence:
    sha: str
    url: str
    collected_at: datetime

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Evidence?{self.sha=}")

    def to_prov_element(self) -> ProvEntity:
        attributes = [
            ("sha", self.sha),
            ("url", self.url),
            ("collected_at", self.collected_at),
            (PROV_TYPE, ProvType.EVIDENCE),
        ]
        return ProvEntity(PLACEHOLDER, self.identifier, attributes)


@dataclass
class Release:
    name: str
    body: str
    tag_name: str
    platform: str
    author: User | None
    assets: list[Asset]
    evidences: list[Evidence]
    created_at: datetime
    released_at: datetime

    @property
    def identifier(self) -> QualifiedName:
        return qualified_name(f"Release?{self.name=}")

    @property
    def creation(self) -> Creation:
        return Creation.from_release(self)

    def to_prov_element(self) -> ProvEntity:
        attributes = [
            ("name", self.name),
            ("body", self.body),
            ("tag_name", self.tag_name),
            ("platform", self.platform),
            ("created_at", self.created_at),
            ("released_at", self.released_at),
            (PROV_TYPE, ProvType.RELEASE),
            (PROV_TYPE, ProvType.COLLECTION),
        ]
        return ProvEntity(PLACEHOLDER, self.identifier, attributes)
