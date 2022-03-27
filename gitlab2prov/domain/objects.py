from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, is_dataclass, Field, field, fields
from typing import Optional, Any, Protocol, Union, Callable
from urllib.parse import urlencode

from prov.identifier import QualifiedName
from prov.model import PROV_LABEL

from gitlab2prov.domain.constants import ProvType, ProvRole, PROV_FIELD_MAP
from gitlab2prov.prov.operations import qualified_name


# metadata for dataclass attributes that relate objects with one another
# such attributes will not be included in the list of prov attributes of a dataclass
IS_RELATION = {"IS_RELATION": True}


Literal = Optional[Union[str, int, datetime]]
Attribute = tuple[str, Literal]


class IsDataclass(Protocol):
    __dataclass_fields__: dict
    __dataclass_params__: dict
    __post_init__: Optional[Callable]


class HasProvType(Protocol):
    prov_type: Union[str, list[str]]


class DataclassWithProvType(HasProvType, IsDataclass):
    pass


def is_relation(field: Field):
    return field.metadata == IS_RELATION


def prov_type(obj: DataclassWithProvType):
    if isinstance(obj.prov_type, list):
        return obj.prov_type[0]
    return obj.prov_type


def prov_identifier(obj: DataclassWithProvType) -> QualifiedName:
    attrs = {f.name: getattr(obj, f.name) for f in fields(obj) if f.repr}
    return qualified_name(f"{prov_type(obj)}?{urlencode(attrs)}")


def prov_label(obj: DataclassWithProvType) -> QualifiedName:
    attrs = [f"{f.name}={getattr(obj, f.name)}" for f in fields(obj) if f.repr]
    return qualified_name(f"{prov_type(obj)}({', '.join(attrs)})")


def prov_attribute_generator(obj: DataclassWithProvType):
    for field in (f for f in fields(obj) if not is_relation(f)):
        key = PROV_FIELD_MAP.get(field.name, field.name)
        if field.type.startswith("list"):
            for val in getattr(obj, field.name):
                yield (key, val)
        else:
            yield (key, getattr(obj, field.name))
    yield (PROV_LABEL, prov_label(obj))


def prov_attributes(obj: DataclassWithProvType) -> list[Attribute]:
    if not is_dataclass(obj) and not isinstance(obj, type):
        raise ValueError(f"{obj} is not an instance of a dataclass!")
    return list(prov_attribute_generator(obj))


@dataclass
class ProvInterface(ABC):
    @property
    def prov_identifier(self) -> QualifiedName:
        return prov_identifier(self)

    @property
    def prov_label(self) -> QualifiedName:
        return prov_label(self)

    @property
    def prov_attributes(self) -> list[Attribute]:
        return prov_attributes(self)

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError


@dataclass
class Agent(ProvInterface):
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_attributes


@dataclass
class Entity(ProvInterface):
    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_attributes


@dataclass(kw_only=True)
class Activity(ProvInterface):
    prov_start: datetime
    prov_end: datetime

    def __iter__(self):
        yield self.prov_identifier
        yield self.prov_start
        yield self.prov_end
        yield self.prov_attributes


@dataclass(unsafe_hash=True, kw_only=True)
class User(Agent):
    name: str
    email: str | None = field(default=None)
    gitlab_username: str | None = field(repr=False, default=None)
    gitlab_id: str | None = field(repr=False, default=None)
    prov_role: ProvRole = field(repr=False, default=None)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.USER)

    def __post_init__(self):
        self.email = self.email.lower() if self.email else None


@dataclass(unsafe_hash=True, kw_only=True)
class File(Entity):
    path: str
    committed_in: str
    prov_type: str = field(init=False, repr=False, default=ProvType.FILE)


@dataclass(unsafe_hash=True, kw_only=True)
class FileRevision(File):
    change_type: str
    original: File = field(repr=False, metadata=IS_RELATION)
    previous: FileRevision | None = field(
        repr=False, default=None, metadata=IS_RELATION
    )
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.FILE_REVISION)


@dataclass(unsafe_hash=True, kw_only=True)
class Annotation(Activity):
    id: str
    type: str
    body: str = field(repr=False)
    kwargs: dict[str, Any] = field(repr=False, default_factory=dict)
    annotator: User = field(repr=False, metadata=IS_RELATION)
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.ANNOTATION)

    @property
    def prov_attributes(self):
        return [*prov_attributes(self), *self.kwargs.items()]


@dataclass(unsafe_hash=True, kw_only=True)
class Version(Entity):
    version_id: str
    prov_type: ProvType = field(repr=False)


@dataclass(unsafe_hash=True, kw_only=True)
class AnnotatedVersion(Entity):
    version_id: str
    annotation_id: str
    prov_type: ProvType = field(repr=False)


@dataclass(unsafe_hash=True, kw_only=True)
class Creation(Activity):
    creation_id: str
    prov_start: datetime = field(repr=False)
    prov_end: datetime = field(repr=False)
    prov_type: ProvType = field(repr=False)


@dataclass(unsafe_hash=True, kw_only=True)
class GitCommit(Activity):
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
class Issue(Entity):
    id: str
    iid: str
    title: str
    description: str = field(repr=False)
    url: str = field(repr=False)
    author: User = field(repr=False, metadata=IS_RELATION)
    annotations: list[Annotation] = field(repr=False, metadata=IS_RELATION)
    created_at: datetime = field(repr=False)
    closed_at: Optional[datetime] = field(repr=False, default=None)
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
class GitlabCommit(Entity):
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
class MergeRequest(Entity):
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
    closed_at: Optional[datetime] = field(repr=False, default=None)
    merged_at: Optional[datetime] = field(repr=False, default=None)
    first_deployed_to_production_at: Optional[datetime] = field(
        repr=False, default=None
    )
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
class Tag(Entity):
    name: str
    hexsha: str
    message: Optional[str] = field(repr=False)
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
class Asset(Entity):
    url: str
    format: str
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.ASSET)


@dataclass(unsafe_hash=True, kw_only=True)
class Evidence(Entity):
    hexsha: str
    url: str
    collected_at: datetime
    prov_type: ProvType = field(init=False, repr=False, default=ProvType.EVIDENCE)


@dataclass(unsafe_hash=True, kw_only=True)
class Release(Entity):
    name: str
    description: str = field(repr=False)
    tag_name: str = field(repr=False)
    author: Optional[User] = field(repr=False, metadata=IS_RELATION)
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
