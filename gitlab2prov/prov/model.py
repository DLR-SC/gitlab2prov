from typing import Optional, Union, Type, Iterable, Callable, Any
from dataclasses import dataclass, field
from operator import attrgetter

from prov.model import (
    ProvDocument,
    ProvDerivation,
    PROV_ROLE,
    PROV_ATTR_STARTTIME,
    ProvInvalidation,
    ProvMembership,
    ProvElement,
    ProvUsage,
    ProvAssociation,
    ProvAttribution,
    ProvGeneration,
    ProvSpecialization,
    ProvCommunication,
    ProvRelation,
    ProvRecord,
)
from prov.identifier import QualifiedName, Namespace
from functools import partial

from gitlab2prov.adapters.repository import Repository
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import (
    FileRevision,
    GitCommit,
    Commit,
    Issue,
    MergeRequest,
    Release,
    GitTag,
    Annotation,
    Creation,
    AnnotatedVersion,
)


AUTHOR_ROLE_MAP = {
    Commit: ProvRole.COMMIT_AUTHOR,
    Issue: ProvRole.ISSUE_AUTHOR,
    MergeRequest: ProvRole.MERGE_REQUEST_AUTHOR,
}


HostedResource = Commit | Issue | MergeRequest
Query = Callable[[Repository], Iterable[HostedResource]]
DEFAULT_NAMESPACE = Namespace("ex", "example.org")


def file_status_query(repository: Repository, status: str):
    for revision in repository.list_all(FileRevision, status=status):
        commit = repository.get(GitCommit, sha=revision.commit)
        for parent in [repository.get(GitCommit, sha=sha) for sha in commit.parents]:
            if status == "modified":
                yield commit, parent, revision, revision.previous
            else:
                yield commit, parent, revision


def hosted_resource_query(repository: Repository, resource_type: Type[HostedResource]):
    for resource in repository.list_all(resource_type):
        if resource_type == Commit:
            yield (resource, repository.get(GitCommit, sha=resource.sha))
        yield (resource, None)


FileAdditionQuery = partial(file_status_query, status="added")
FileDeletionQuery = partial(file_status_query, status="deleted")
FileModificationQuery = partial(file_status_query, status="modified")
HostedCommitQuery = partial(hosted_resource_query, resource_type=Commit)
HostedIssueQuery = partial(hosted_resource_query, resource_type=Issue)
HostedMergeQuery = partial(hosted_resource_query, resource_type=MergeRequest)


@dataclass
class ProvenanceContext:
    document: ProvDocument
    namespace: Optional[str] = None

    def add_element(self, dataclass_instance) -> ProvRecord:
        # Convert the dataclass instance to a ProvElement
        element = self.convert_to_prov_element(dataclass_instance)
        # Add the namespace to the element if it is provided
        if self.namespace:
            element.add_namespace(self.namespace)
        # Return the newly added element
        return self.document.add_record(element)

    def convert_to_prov_element(self, dataclass_instance) -> ProvElement:
        # Convert the dataclass instance to a ProvElement
        element = dataclass_instance.to_prov_element()
        # Add the element to the ProvDocument and return it
        return self.document.new_record(element._prov_type, element.identifier, element.attributes)

    def add_relation(
        self,
        source_dataclass_instance,
        target_dataclass_instance,
        relationship_type: Type[ProvRelation],
        attributes: dict[str, Any] = None,
    ) -> None:
        # Initialize attributes if they are not provided
        if not attributes:
            attributes = dict()
        # Make sure that both source and target are part of the document
        source = self.add_element(source_dataclass_instance)
        target = self.add_element(target_dataclass_instance)
        # Create a relationship between the source and target
        relationship = self.document.new_record(
            relationship_type._prov_type,
            QualifiedName(DEFAULT_NAMESPACE, f"relation:{source.identifier}:{target.identifier}"),
            {
                relationship_type.FORMAL_ATTRIBUTES[0]: source,
                relationship_type.FORMAL_ATTRIBUTES[1]: target,
            },
        )
        # Add the remaining attributes to the relationship
        relationship.add_attributes(attributes)
        # Add the relationship to the ProvDocument
        self.document.add_record(relationship)

    def get_document(self):
        return self.document


@dataclass
class FileAdditionModel:
    commit: GitCommit
    parent: GitCommit
    revision: FileRevision
    ctx: ProvenanceContext = field(init=False)

    def __post_init__(self):
        self.ctx = ProvenanceContext(ProvDocument())

    def build_provenance_model(self) -> ProvDocument:
        # Add the elements to the context
        self.ctx.add_element(self.commit)
        self.ctx.add_element(self.commit.author)
        self.ctx.add_element(self.commit.committer)
        self.ctx.add_element(self.revision)
        self.ctx.add_element(self.revision.file)
        # Check if parent exists
        if self.parent:
            # Add the parent to the context
            self.ctx.add_element(self.parent)
            # Add the communication relation (wasInformedBy) between the parent and the commit
            self.ctx.add_relation(self.commit, self.parent, ProvCommunication, {})
        # Add the relations to the context
        self.ctx.add_relation(
            self.commit,
            self.commit.author,
            ProvAssociation,
            {PROV_ROLE: ProvRole.AUTHOR},
        )
        self.ctx.add_relation(
            self.commit,
            self.commit.committer,
            ProvAssociation,
            {PROV_ROLE: ProvRole.COMMITTER},
        )
        self.ctx.add_relation(
            self.revision,
            self.commit,
            ProvGeneration,
            {
                PROV_ATTR_STARTTIME: self.commit.start,
                PROV_ROLE: ProvRole.FILE,
            },
        )
        self.ctx.add_relation(
            self.revision.file,
            self.commit,
            ProvGeneration,
            {
                PROV_ATTR_STARTTIME: self.commit.start,
                PROV_ROLE: ProvRole.ADDED_REVISION,
            },
        )
        self.ctx.add_relation(self.revision.file, self.commit.author, ProvAttribution)
        self.ctx.add_relation(self.revision, self.revision.file, ProvSpecialization)
        # Return the document
        return self.ctx.get_document()


@dataclass
class FileDeletionModel:
    commit: GitCommit
    parent: GitCommit
    revision: FileRevision
    ctx: ProvenanceContext = field(init=False)

    def __post_init__(self):
        # Initialize the context
        self.ctx = ProvenanceContext(ProvDocument())

    def build_provenance_model(self) -> ProvDocument:
        # Add the elements to the context
        self.ctx.add_element(self.commit)
        self.ctx.add_element(self.revision)
        self.ctx.add_element(self.revision.file)
        self.ctx.add_element(self.commit.author)
        self.ctx.add_element(self.commit.committer)
        # Check if parent exists
        if self.parent:
            # Add the parent to the context
            self.ctx.add_element(self.parent)
            # Add the communication relation (wasInformedBy) between the parent and the commit
            self.ctx.add_relation(self.commit, self.parent, ProvCommunication)
        # Add the relations to the context
        self.ctx.add_relation(
            self.commit, self.commit.committer, ProvAssociation, {PROV_ROLE: ProvRole.COMMITTER}
        )
        self.ctx.add_relation(
            self.commit, self.commit.author, ProvAssociation, {PROV_ROLE: ProvRole.AUTHOR}
        )
        self.ctx.add_relation(self.revision, self.revision.file, ProvSpecialization)
        self.ctx.add_relation(
            self.revision,
            self.commit,
            ProvInvalidation,
            {PROV_ATTR_STARTTIME: self.commit.start, PROV_ROLE: ProvRole.DELETED_REVISION},
        )
        # Return the document
        return self.ctx.get_document()


@dataclass
class FileModificationModel:
    commit: GitCommit
    parent: GitCommit
    revision: FileRevision
    previous: FileRevision
    ctx: ProvenanceContext = field(init=False)

    def __post_init__(self):
        # Initialize the context
        self.ctx = ProvenanceContext(ProvDocument())

    def build_provenance_model(self) -> ProvDocument:
        # Add the elements to the context
        self.ctx.add_element(self.commit)
        self.ctx.add_element(self.revision)
        self.ctx.add_element(self.revision.file)
        self.ctx.add_element(self.previous)
        self.ctx.add_element(self.commit.author)
        self.ctx.add_element(self.commit.committer)
        # Check if parent exists
        if self.parent:
            # Add the parent to the context
            self.ctx.add_element(self.parent)
            # Add the communication relation (wasInformedBy) between the parent and the commit
            self.ctx.add_relation(self.commit, self.parent, ProvCommunication)
        # Add the relations to the context
        self.ctx.add_relation(
            self.commit, self.commit.author, ProvAssociation, {PROV_ROLE: ProvRole.AUTHOR}
        )
        self.ctx.add_relation(
            self.commit, self.commit.committer, ProvAssociation, {PROV_ROLE: ProvRole.COMMITTER}
        )
        self.ctx.add_relation(self.revision, self.revision.file, ProvSpecialization)
        self.ctx.add_relation(
            self.revision,
            self.commit,
            ProvGeneration,
            {PROV_ATTR_STARTTIME: self.commit.start, PROV_ROLE: ProvRole.MODIFIED_REVISION},
        )
        self.ctx.add_relation(self.revision, self.commit.author, ProvAttribution)
        self.ctx.add_relation(
            self.revision, self.previous, ProvDerivation
        )  # TODO: has to be wasRevisionOf record, add asserted type 'Revison'
        self.ctx.add_relation(
            self.commit,
            self.previous,
            ProvUsage,
            {PROV_ATTR_STARTTIME: self.commit.start, PROV_ROLE: ProvRole.PREVIOUS_REVISION},
        )
        # Return the document
        return self.ctx.get_document()


@dataclass
class HostedResourceModel:
    """Model for a hosted resource (e.g., commit, issue, merge request)."""

    resource: Union[Commit, Issue, MergeRequest]
    commit: Optional[GitCommit] = None
    ctx: ProvenanceContext = field(init=False)

    def __post_init__(self):
        # Initialize the context
        self.ctx = ProvenanceContext(ProvDocument())

    def build_provenance_model(self):
        # Choose the creation part based on the type of resource
        if isinstance(self.resource, Commit) and self.commit:
            self._add_creation_part_for_hosted_commits()
        else:
            self._add_creation_part()
        # Set the previous annotation and version to the creation / original version
        previous_annotation = self.resource.creation
        previous_version = self.resource.first_version
        # For each annotation and version, add the annotation part, sort by time ascending
        for current_annotation, current_version in zip(
            sorted(self.resource.annotations, key=attrgetter("start")),
            sorted(self.resource.annotated_versions, key=attrgetter("start")),
        ):
            # Add the annotation chain link
            self._add_annotation_part(
                current_annotation,
                previous_annotation,
                current_version,
                previous_version,
            )
            # Update the previous annotation and version
            previous_annotation = current_annotation
            previous_version = current_version

        return self.ctx.get_document()

    def _add_creation_part_for_hosted_commits(self):
        # Add the elements to the context
        self.ctx.add_element(self.resource)
        self.ctx.add_element(self.resource.creation)
        self.ctx.add_element(self.resource.first_version)
        self.ctx.add_element(self.resource.author)
        self.ctx.add_element(self.commit)
        self.ctx.add_element(self.commit.committer)
        # Add the relations to the context
        self.ctx.add_relation(
            self.resource.creation,
            self.resource.author,
            ProvAssociation,
            {PROV_ROLE: ProvRole.COMMIT_AUTHOR},
        )
        self.ctx.add_relation(self.resource, self.resource.author, ProvAttribution)
        self.ctx.add_relation(self.resource.first_version, self.resource, ProvSpecialization)
        self.ctx.add_relation(self.resource.first_version, self.resource.author, ProvAttribution)
        self.ctx.add_relation(
            self.resource,
            self.resource.creation,
            ProvGeneration,
            {PROV_ATTR_STARTTIME: self.resource.creation.start, PROV_ROLE: ProvRole.RESOURCE},
        )
        self.ctx.add_relation(
            self.resource.first_version,
            self.resource.creation,
            ProvGeneration,
            {
                PROV_ATTR_STARTTIME: self.resource.creation.start,
                PROV_ROLE: ProvRole.FIRST_RESOURCE_VERSION,
            },
        )
        self.ctx.add_relation(self.resource.creation, self.commit, ProvCommunication)
        self.ctx.add_relation(
            self.commit,
            self.commit.committer,
            ProvAssociation,
            {PROV_ROLE: ProvRole.COMMIT_AUTHOR},
        )

    def _add_creation_part(self):
        self.ctx.add_element(self.resource)
        self.ctx.add_element(self.resource.creation)
        self.ctx.add_element(self.resource.first_version)
        self.ctx.add_element(self.resource.author)

        self.ctx.add_relation(self.resource, self.resource.author, ProvAttribution)
        self.ctx.add_relation(self.resource.first_version, self.resource, ProvSpecialization)
        self.ctx.add_relation(self.resource.first_version, self.resource.author, ProvAttribution)
        self.ctx.add_relation(
            self.resource.creation,
            self.resource.author,
            ProvAssociation,
            {PROV_ROLE: AUTHOR_ROLE_MAP[type(self.resource)]},
        )
        self.ctx.add_relation(
            self.resource,
            self.resource.creation,
            ProvGeneration,
            {PROV_ATTR_STARTTIME: self.resource.creation.start, PROV_ROLE: ProvRole.RESOURCE},
        )
        self.ctx.add_relation(
            self.resource.first_version,
            self.resource.creation,
            ProvGeneration,
            {
                PROV_ATTR_STARTTIME: self.resource.creation.start,
                PROV_ROLE: ProvRole.FIRST_RESOURCE_VERSION,
            },
        )

    def _add_annotation_part(
        self,
        current_annotation: Annotation,
        previous_annotation: Union[Annotation, Creation],
        current_version: AnnotatedVersion,
        previous_version: AnnotatedVersion,
    ):
        # Add the elements to the context
        self.ctx.add_element(self.resource)
        self.ctx.add_element(self.resource.creation)
        self.ctx.add_element(current_annotation)
        self.ctx.add_element(current_annotation.annotator)
        self.ctx.add_element(current_version)
        self.ctx.add_element(previous_annotation)
        self.ctx.add_element(previous_version)
        # Add the relations to the context
        self.ctx.add_relation(current_annotation, previous_annotation, ProvCommunication)
        self.ctx.add_relation(current_version, previous_version, ProvDerivation)
        self.ctx.add_relation(current_version, current_annotation.annotator, ProvAttribution)
        self.ctx.add_relation(
            current_annotation,
            current_annotation.annotator,
            ProvAssociation,
            {PROV_ROLE: ProvRole.ANNOTATOR},
        )
        self.ctx.add_relation(
            current_annotation,
            previous_version,
            ProvUsage,
            {
                PROV_ATTR_STARTTIME: current_annotation.start,
                PROV_ROLE: ProvRole.PRE_ANNOTATION_VERSION,
            },
        )
        self.ctx.add_relation(
            current_version,
            current_annotation,
            ProvGeneration,
            {
                PROV_ATTR_STARTTIME: current_annotation.start,
                PROV_ROLE: ProvRole.POST_ANNOTATION_VERSION,
            },
        )


@dataclass
class ReleaseModel:
    release: Release
    tag: GitTag
    ctx: ProvenanceContext = field(init=False)

    def __post_init__(self):
        self.ctx = ProvenanceContext(ProvDocument())

    @staticmethod
    def query(repository: Repository) -> Iterable[tuple[Release, GitTag]]:
        for release in repository.list_all(Release):
            tag = repository.get(GitTag, sha=release.tag_sha)
            yield release, tag

    def build_provenance_model(self) -> ProvDocument:
        # Add the release
        self.ctx.add_element(self.release)
        self.ctx.add_element(self.release.author)
        self.ctx.add_element(self.release.creation)
        # Add all evidence files
        for evidence in self.release.evidences:
            self.ctx.add_element(evidence)
        # Add all assets
        for asset in self.release.assets:
            self.ctx.add_element(asset)
        # Add the tag
        self.ctx.add_element(self.tag)
        self.ctx.add_element(self.tag.creation)
        self.ctx.add_element(self.tag.author)
        # Add the release relationships
        self.ctx.add_relation(self.release, self.release.author, ProvAttribution)
        self.ctx.add_relation(
            self.release,
            self.release.creation,
            ProvGeneration,
            {PROV_ATTR_STARTTIME: self.release.creation.start, PROV_ROLE: ProvRole.RELEASE},
        )
        self.ctx.add_relation(
            self.release.creation,
            self.release.author,
            ProvAssociation,
            {PROV_ROLE: ProvRole.RELEASE_AUTHOR},
        )
        # Add the evidence and asset relationships
        for evidence in self.release.evidences:
            self.ctx.add_relation(evidence, self.release, ProvMembership)
            self.ctx.add_relation(evidence, self.release.creation, ProvGeneration)
        for asset in self.release.assets:
            self.ctx.add_relation(asset, self.release, ProvMembership)
            self.ctx.add_relation(asset, self.release.creation, ProvGeneration)
        # Add tag relationships
        self.ctx.add_relation(self.tag, self.release, ProvMembership)
        self.ctx.add_relation(self.tag, self.tag.author, ProvAttribution)
        self.ctx.add_relation(
            self.tag,
            self.tag.creation,
            ProvGeneration,
            {PROV_ATTR_STARTTIME: self.tag.creation.start, PROV_ROLE: ProvRole.TAG},
        )
        self.ctx.add_relation(
            self.tag.creation, self.tag.author, ProvAssociation, {PROV_ROLE: ProvRole.TAG_AUTHOR}
        )


@dataclass
class GitTagModel:
    """Model for a Git tag."""

    tag: GitTag
    commit: Commit | None = None
    ctx: ProvenanceContext = field(init=False)

    def __post_init__(self):
        self.ctx = ProvenanceContext(ProvDocument())

    @staticmethod
    def query(repository: Repository) -> Iterable[tuple[GitTag, Commit]]:
        for tag in repository.list_all(GitTag):
            commit = repository.get(Commit, sha=tag.sha)
            yield tag, commit

    def build_provenance_model(self) -> ProvDocument:
        # Add the tag
        self.ctx.add_element(self.tag)
        self.ctx.add_element(self.tag.creation)
        self.ctx.add_element(self.tag.author)
        # Add the commit
        if self.commit:
            self.ctx.add_element(self.commit)
            self.ctx.add_element(self.commit.creation)
            self.ctx.add_element(self.commit.author)
        # Add tag relationships
        self.ctx.add_relation(
            self.tag,
            self.tag.creation,
            ProvGeneration,
            {PROV_ATTR_STARTTIME: self.tag.creation.start, PROV_ROLE: ProvRole.TAG},
        )
        self.ctx.add_relation(self.tag, self.tag.author, ProvAttribution)
        self.ctx.add_relation(
            self.tag.creation, self.tag.author, ProvAssociation, {PROV_ROLE: ProvRole.TAG_AUTHOR}
        )
        # Add commit relationships
        if self.commit:
            self.ctx.add_relation(self.commit, self.tag, ProvMembership)
            self.ctx.add_relation(
                self.commit,
                self.commit.creation,
                ProvGeneration,
                {PROV_ATTR_STARTTIME: self.commit.creation.start, PROV_ROLE: ProvRole.COMMIT},
            )
            self.ctx.add_relation(self.commit, self.commit.author, ProvAttribution)
            self.ctx.add_relation(
                self.commit.creation,
                self.commit.author,
                ProvAssociation,
                {PROV_ROLE: ProvRole.COMMIT_AUTHOR},
            )
        return self.ctx.get_document()


@dataclass
class CallableModel:
    """A model that can be called to build a provenance document."""

    model: Type[
        FileAdditionModel
        | FileModificationModel
        | FileDeletionModel
        | HostedResourceModel
        | GitTagModel
        | ReleaseModel
    ]
    query: Query
    document: ProvDocument = field(init=False)

    def __post_init__(self):
        # Initialize the document
        self.document = ProvDocument()

    def __call__(self, repository: Repository):
        # Pass the repository to the query
        for args in self.query(repository):
            # Initialize the model
            m = self.model(*args)
            # Update the document with the model
            self.document.update(m.build_provenance_model())
        return self.document


MODELS = [
    CallableModel(FileAdditionModel, FileAdditionQuery),
    CallableModel(FileDeletionModel, FileDeletionQuery),
    CallableModel(FileModificationModel, FileModificationQuery),
    CallableModel(HostedResourceModel, HostedIssueQuery),
    CallableModel(HostedResourceModel, HostedCommitQuery),
    CallableModel(HostedResourceModel, HostedMergeQuery),
    CallableModel(ReleaseModel, ReleaseModel.query),
    CallableModel(GitTagModel, GitTagModel.query),
]
