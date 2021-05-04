from typing import List, Union
from prov.model import ProvDocument, ProvElement, ProvRelation
from ..procs.meta import Addition, CommitCreationPackage, CommitModelPackage, ResourceCreationPackage, Deletion, \
    Modification, ResourceModelPackage


def create_graph(packages: List[Union[CommitModelPackage, ResourceModelPackage]]) -> ProvDocument:
    """Create graph from list of packages.

    Choose graph model according to package type.
    Remove duplicated specializationOf relations.
    """
    graph = ProvDocument()
    graph.set_default_namespace("gitlab2prov")

    if not packages:
        return graph

    model = {
        CommitModelPackage: commit_package_model,
        ResourceModelPackage: resource_package_model,
    }[type(packages[0])]

    graph = model(graph, packages)
    graph = enforce_uniqueness_constraints(graph)
    return graph


def enforce_uniqueness_constraints(graph: ProvDocument) -> ProvDocument:
    """Enforce model uniqueness constraints.

    Remove node duplicates:
        - ProvDocument.unified takes care of this by removing nodes with
        the same id.

    Remove relation duplicates:
        - Allow only one relation of a certain type between two nodes.

    Enforcing this constraint after having populated the model instead of
    during population simplifies the model creation.
    """
    records, known = [], set()

    for relation in graph.get_records(ProvRelation):
        (_, source), (_, target) = relation.formal_attributes[:2]
        rel_tuple = (type(relation), source, target)
        if rel_tuple in known:
            continue
        known.add(rel_tuple)
        records.append(relation)

    records.extend(graph.get_records(ProvElement))

    g = ProvDocument(records)
    return g.unified()


def commit_package_model(graph: ProvDocument, packages: List[CommitModelPackage]) -> ProvDocument:
    """Commit model implementation."""
    for package in packages:
        graph = add_commit(graph, package)
        graph = add_parents(graph, package)
        graph = add_diffs(graph, package)
    return graph


def add_commit(graph: ProvDocument, package: CommitModelPackage) -> ProvDocument:
    """Add commit activity, agents for author and committer, relations between agents and activity."""
    author, committer, commit = package.author, package.committer, package.commit
    graph.agent(*author)
    graph.agent(*committer)
    graph.activity(*commit)
    graph.wasAssociatedWith(commit.id, author.id)
    graph.wasAssociatedWith(commit.id, committer.id)
    return graph


def add_parents(graph: ProvDocument, package: CommitModelPackage) -> ProvDocument:
    """Add link between commit activities and their parents."""
    commit = package.commit
    for parent in package.parent_commits:
        graph.activity(*parent)
        graph.activity(*commit)
        graph.wasInformedBy(commit.id, parent.id)
    return graph


def add_diffs(graph: ProvDocument, package: CommitModelPackage) -> ProvDocument:
    """Add file change models according to their type."""
    for action in package.file_changes:
        action_model = {
            Addition: addition,
            Deletion: deletion,
            Modification: modification
        }[type(action)]
        graph = action_model(graph, package, action)
    return graph


def addition(graph: ProvDocument, package: CommitModelPackage, action: Addition) -> ProvDocument:
    """Add model for a newly added file."""
    file, file_version = action
    author, commit = package.author, package.commit
    graph.entity(*file)
    graph.entity(*file_version)
    graph.wasGeneratedBy(file.id, commit.id)
    graph.wasGeneratedBy(file_version.id, commit.id)
    graph.wasAttributedTo(file.id, author.id)
    graph.wasAttributedTo(file_version.id, author.id)
    graph.specializationOf(file_version.id, file.id)
    return graph


def deletion(graph: ProvDocument, package: CommitModelPackage, action: Deletion) -> ProvDocument:
    """Add model for a deleted file."""
    file, file_version = action
    commit = package.commit
    graph.entity(*file)
    graph.entity(*file_version)
    graph.specializationOf(file_version.id, file.id)
    graph.wasInvalidatedBy(file_version.id, commit.id)
    return graph


def modification(graph: ProvDocument, package: CommitModelPackage, action: Modification) -> ProvDocument:
    """Add model for a modified file."""
    file, file_version, previous_versions = action
    author, commit = package.author, package.commit
    graph.entity(*file)
    graph.entity(*file_version)
    graph.wasAttributedTo(file_version.id, author.id)
    graph.wasGeneratedBy(file_version.id, commit.id)
    graph.specializationOf(file_version.id, file.id)
    for version in previous_versions:
        graph.entity(*version)
        graph.used(commit.id, version.id)
        graph.wasRevisionOf(file_version.id, version.id)
        graph.specializationOf(version.id, file.id)
    return graph


def resource_package_model(graph: ProvDocument, packages: List[ResourceModelPackage]) -> ProvDocument:
    """Resource model implementation.

    Choose model for creation according to the type of the creation package.
    """
    for package in packages:
        add_creation = {
            CommitCreationPackage:  add_commit_creation,
            ResourceCreationPackage: add_resource_creation,
        }[type(package.creation)]
        graph = add_creation(graph, package)
        graph = add_event_chain(graph, package)
    return graph


def add_commit_creation(graph: ProvDocument, package: ResourceModelPackage) -> ProvDocument:
    """Add model for commit creation."""
    committer, commit, creation, resource, resource_version = package.creation
    graph.activity(*commit)
    graph.activity(*creation)
    graph.agent(*committer)
    graph.entity(*resource)
    graph.entity(*resource_version)
    graph.wasAssociatedWith(commit.id, committer.id)
    graph.wasAssociatedWith(creation.id, committer.id)
    graph.wasAttributedTo(resource.id, committer.id)
    graph.wasGeneratedBy(resource.id, creation.id)
    graph.wasGeneratedBy(resource_version.id, creation.id)
    graph.specializationOf(resource_version.id, resource.id)
    graph.wasInformedBy(creation.id, commit.id)
    return graph


def add_resource_creation(graph: ProvDocument, package: ResourceModelPackage) -> ProvDocument:
    """Add model for resource creation."""
    creator, creation, resource, resource_version = package.creation
    graph.activity(*creation)
    graph.entity(*resource)
    graph.entity(*resource_version)
    graph.agent(*creator)
    graph.wasAssociatedWith(creation.id, creator.id)
    graph.wasAttributedTo(resource.id, creator.id)
    graph.wasAttributedTo(resource_version.id, creator.id)
    graph.wasGeneratedBy(resource.id, creation.id)
    graph.wasGeneratedBy(resource_version.id, creation.id)
    graph.specializationOf(resource_version.id, resource.id)
    return graph


def add_event_chain(graph: ProvDocument, package: ResourceModelPackage) -> ProvDocument:
    """Add chain of events beginning at the creation event."""
    previous_event = previous_resource_version = None
    for chain_link in package.event_chain:
        user, event, resource, resource_version = chain_link
        graph.entity(*resource)
        graph.entity(*resource_version)
        graph.activity(*event)
        graph.agent(*user)
        graph.wasAssociatedWith(event.id, user.id)
        graph.wasAttributedTo(resource_version.id, user.id)
        graph.specializationOf(resource_version.id, resource.id)
        if previous_event is not None and previous_resource_version is not None:
            graph.entity(*previous_resource_version)
            graph.activity(*previous_event)
            graph.wasGeneratedBy(resource_version.id, event.id)
            graph.used(event.id, previous_resource_version.id)
            graph.wasDerivedFrom(resource_version.id, previous_resource_version.id)
            graph.wasInformedBy(event.id, previous_event.id)
        previous_event = event
        previous_resource_version = resource_version
    return graph
