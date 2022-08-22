from __future__ import annotations

from dataclasses import dataclass
from dataclasses import Field
from dataclasses import field
from dataclasses import fields
from datetime import datetime
from itertools import cycle
from typing import Any
from urllib.parse import urlencode

from prov.identifier import QualifiedName
from prov.model import PROV_LABEL

from gitlab2prov.domain.constants import PROV_FIELD_MAP
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.constants import ProvType
from gitlab2prov.prov.operations import qualified_name


# metadata for dataclass attributes that relate objects with one another
# such attributes will not be included in the list of prov attributes of a dataclass
IS_RELATION = {"IS_RELATION": True}


def is_relation(field: Field):
    return field.metadata == IS_RELATION


class ProvMixin:
    @property
    def prov_identifier(self) -> QualifiedName:
        attrs = urlencode(dict(self._traverse_repr_fields()))
        label = f"{self._prov_type()}?{attrs}"
        return qualified_name(label)

    @property
    def prov_label(self) -> QualifiedName:
        attrs = urlencode(dict(self._traverse_repr_fields()))
        label = f"{self._prov_type()}?{attrs}"
        return qualified_name(label)

    @property
    def prov_attributes(self) -> list[tuple[str, str | int | datetime | None]]:
        return list(self._traverse_attributes())

    def _prov_type(self) -> str:
        match self.prov_type:
            case list():
                return self.prov_type[0]
            case _:
                return self.prov_type

    def _traverse_repr_fields(self):
        for f in fields(self):
            if f.repr:
                yield f.name, getattr(self, f.name)

    def _traverse_attributes(self):
        for f in fields(self):
            if not is_relation(f):
                yield from self._expand_attribute(f.name, getattr(self, f.name))
        yield (PROV_LABEL, self.prov_label)

    def _expand_attribute(self, key, val):
        key = PROV_FIELD_MAP.get(key, key)
        match val:
            case list():
                yield from zip(cycle([key]), val)
            case dict():
                yield from val.items()
            case _:
                yield key, val


@dataclass
class AgentMixin:
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_attributes


@dataclass
class EntityMixin:
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_attributes


@dataclass(kw_only=True)
class ActivityMixin:
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_start
        yield self.prov_end
        yield self.prov_attributes


@dataclass(unsafe_hash=True, kw_only=True)
class User(ProvMixin, AgentMixin):
    name: str
    email: str | None = field(default=None)
    gitlab_username: str | None = field(repr=False, default=None)
    gitlab_id: str | None = field(repr=False, default=None)
    prov_role: ProvRole = field(repr=False, default=None)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.USER)

    def __post_init__(self):
        self.email = self.email.lower() if self.email else None


@dataclass(unsafe_hash=True, kw_only=True)
class File(ProvMixin, EntityMixin):
    path: str
    committed_in: str
    prov_type: str = field(init=False, repr=False, default=ProvType.FILE)


@dataclass(unsafe_hash=True, kw_only=True)
class FileRevision(ProvMixin, EntityMixin):
    path: str
    committed_in: str
    change_type: str
    original: File = field(repr=False, metadata=IS_RELATION)
    previous: FileRevision | None = field(
        repr=False, default=None, metadata=IS_RELATION
    )
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.FILE_REVISION)


@dataclass(unsafe_hash=True, kw_only=True)
class Annotation(ProvMixin, ActivityMixin):
    id: str
    type: str
    body: str = field(repr=False)
    kwargs: dict[str, Any] = field(repr=False, default_factory=dict)
    annotator: User = field(repr=False, metadata=IS_RELATION)
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.ANNOTATION)


@dataclass(unsafe_hash=True, kw_only=True)
class Version(ProvMixin, EntityMixin):
    version_id: str
    prov_type: ProvType = field(repr=False)


@dataclass(unsafe_hash=True, kw_only=True)
class AnnotatedVersion(ProvMixin, EntityMixin):
    version_id: str
    annotation_id: str
    prov_type: ProvType = field(repr=False)


@dataclass(unsafe_hash=True, kw_only=True)
class Creation(ProvMixin, ActivityMixin):
    creation_id: str
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: ProvType = field(repr=False)


@dataclass(unsafe_hash=True, kw_only=True)
class GitCommit(ProvMixin, ActivityMixin):
    hexsha: str
    message: str = field(repr=False)
    title: str = field(repr=False)
    author: User = field(repr=False, metadata=IS_RELATION)
    committer: User = field(repr=False, metadata=IS_RELATION)
    parents: list[str] = field(repr=False, metadata=IS_RELATION)
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.GIT_COMMIT)


@dataclass(unsafe_hash=True, kw_only=True)
class Issue(ProvMixin, EntityMixin):
    id: str
    iid: str
    title: str
    description: str = field(repr=False)
    url: str = field(repr=False)
    author: User = field(repr=False, metadata=IS_RELATION)
    annotations: list[Annotation] = field(repr=False, metadata=IS_RELATION)
    created_at: datetime = field(repr=False)
    closed_at: datetime | None = field(repr=False, default=None)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.ISSUE)

    @property
    def creation(self) -> Creation:
        return Creation(
            creation_id=self.id,
            prov_start=self.created_at,
            prov_end=self.closed_at,
            prov_type=ProvType.ISSUE_CREATION,
        )

    @property
    def first_version(self) -> Version:
        return Version(version_id=self.id, prov_type=ProvType.ISSUE_VERSION)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion(
                version_id=self.id,
                annotation_id=annotation.id,
                prov_type=ProvType.ISSUE_VERSION_ANNOTATED,
            )
            for annotation in self.annotations
        ]


@dataclass(unsafe_hash=True, kw_only=True)
class GitlabCommit(ProvMixin, EntityMixin):
    hexsha: str
    url: str = field(repr=False)
    author: User = field(repr=False, metadata=IS_RELATION)
    annotations: list[Annotation] = field(repr=False, metadata=IS_RELATION)
    authored_at: datetime = field(repr=False)
    committed_at: datetime = field(repr=False)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.GITLAB_COMMIT)

    @property
    def creation(self) -> Creation:
        return Creation(
            creation_id=self.hexsha,
            prov_start=self.authored_at,
            prov_end=self.committed_at,
            prov_type=ProvType.GITLAB_COMMIT_CREATION,
        )

    @property
    def first_version(self) -> Version:
        return Version(version_id=self.hexsha, prov_type=ProvType.GITLAB_COMMIT_VERSION)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion(
                version_id=self.hexsha,
                annotation_id=annotation.id,
                prov_type=ProvType.GITLAB_COMMIT_VERSION_ANNOTATED,
            )
            for annotation in self.annotations
        ]


@dataclass(unsafe_hash=True, kw_only=True)
class MergeRequest(ProvMixin, EntityMixin):
    id: str
    iid: str
    title: str
    description: str = field(repr=False)
    url: str = field(repr=False)
    source_branch: str = field(repr=False)
    target_branch: str = field(repr=False)
    author: User = field(repr=False, metadata=IS_RELATION)
    annotations: list[Annotation] = field(repr=False, metadata=IS_RELATION)
    created_at: datetime = field(repr=False)
    closed_at: datetime | None = field(repr=False, default=None)
    merged_at: datetime | None = field(repr=False, default=None)
    first_deployed_to_production_at: datetime | None = field(repr=False, default=None)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.MERGE_REQUEST)

    @property
    def creation(self) -> Creation:
        return Creation(
            creation_id=self.id,
            prov_start=self.created_at,
            prov_end=self.closed_at,
            prov_type=ProvType.MERGE_REQUEST_CREATION,
        )

    @property
    def first_version(self) -> Version:
        return Version(version_id=self.id, prov_type=ProvType.MERGE_REQUEST_VERSION)

    @property
    def annotated_versions(self) -> list[AnnotatedVersion]:
        return [
            AnnotatedVersion(
                version_id=self.id,
                annotation_id=annotation.id,
                prov_type=ProvType.MERGE_REQUEST_VERSION_ANNOTATED,
            )
            for annotation in self.annotations
        ]


@dataclass(unsafe_hash=True, kw_only=True)
class Tag(ProvMixin, EntityMixin):
    name: str
    hexsha: str
    message: str | None = field(repr=False)
    author: User = field(repr=False, metadata=IS_RELATION)
    created_at: datetime = field(repr=False)
    prov_type: list[ProvType] = field(
        init=False,
        repr=False,
        default_factory=lambda: [ProvType.TAG, ProvType.COLLECTION],
    )

    @property
    def creation(self) -> Creation:
        return Creation(
            creation_id=self.name,
            prov_start=self.created_at,
            prov_end=self.created_at,
            prov_type=ProvType.TAG_CREATION,
        )


@dataclass(unsafe_hash=True, kw_only=True)
class Asset(ProvMixin, EntityMixin):
    url: str
    format: str
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.ASSET)


@dataclass(unsafe_hash=True, kw_only=True)
class Evidence(ProvMixin, EntityMixin):
    hexsha: str
    url: str
    collected_at: datetime
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.EVIDENCE)


@dataclass(unsafe_hash=True, kw_only=True)
class Release(ProvMixin, EntityMixin):
    name: str
    description: str = field(repr=False)
    tag_name: str = field(repr=False)
    author: User | None = field(repr=False, metadata=IS_RELATION)
    assets: list[Asset] = field(repr=False, metadata=IS_RELATION)
    evidences: list[Evidence] = field(repr=False, metadata=IS_RELATION)
    created_at: datetime = field(repr=False)
    released_at: datetime = field(repr=False)
    prov_type: list[ProvType] = field(
        init=False,
        repr=False,
        default_factory=lambda: [ProvType.RELEASE, ProvType.COLLECTION],
    )

    @property
    def creation(self) -> Creation:
        return Creation(
            creation_id=self.name,
            prov_start=self.created_at,
            prov_end=self.released_at,
            prov_type=ProvType.RELEASE_CREATION,
        )
