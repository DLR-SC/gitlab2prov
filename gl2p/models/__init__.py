from prov.model import ProvDocument
from ..procs.meta import Addition, CommitCreationPackage, CommitModelPackage, ResourceCreationPackage, Deletion, EventPackage, \
    Modification, ResourceModelPackage


def create_graph(packages):
    graph = ProvDocument()
    graph.set_default_namespace("gitlab2prov")
    if not packages:
        return graph
    model = {
        CommitModelPackage: commit_package_model,
        ResourceModelPackage: resource_package_model,
    }[type(packages[0])]  # choose model according to package type
    graph = model(graph, packages)
    return graph
    # return remove_duplicates(graph)


def remove_duplicates(graph: ProvDocument):
    """Remove all duplicate nodes by identifier.

    Enforces cardinality constraint of at most one specializationOf relation
    per node to remove relations that have been duplicated by mistake.
    """
    unified = graph.unified()
    records = set(unified.get_records())
    duplicates_removed = ProvDocument(records)
    return duplicates_removed


def commit_package_model(graph, packages):
    for pkg in packages:
        graph = add_commit(graph, pkg)
        graph = add_parents(graph, pkg)
        graph = add_diffs(graph, pkg)
    return graph


def add_commit(graph, pkg):
    author, committer, commit = pkg.author, pkg.committer, pkg.commit
    graph.agent(*author)
    graph.agent(*committer)
    graph.activity(*commit)
    graph.wasAssociatedWith(commit.id, author.id)
    graph.wasAssociatedWith(commit.id, committer.id)
    return graph


def add_parents(graph, pkg):
    commit = pkg.commit
    for parent in pkg.parent_commits:
        graph.activity(*parent)
        graph.activity(*commit)
        graph.wasInformedBy(commit.id, parent.id)
    return graph


def add_diffs(graph, pkg):
    # distinguish between addition, modification, deletion
    for action in pkg.file_changes:
        action_model = {
            Addition: addition,
            Deletion: deletion,
            Modification: modification
        }[type(action)]
        graph = action_model(graph, pkg, action)
    return graph


def addition(graph, pkg, action):
    file, file_version = action
    author, commit = pkg.author, pkg.commit
    graph.entity(*file)
    graph.entity(*file_version)
    graph.wasGeneratedBy(file.id, commit.id)
    graph.wasGeneratedBy(file_version.id, commit.id)
    graph.wasAttributedTo(file.id, author.id)
    graph.wasAttributedTo(file_version.id, author.id)
    graph.specializationOf(file_version.id, file.id)
    return graph


def deletion(graph, pkg, action):
    file, file_version = action
    author, commit = pkg.author, pkg.commit
    graph.entity(*file)
    graph.entity(*file_version)
    graph.specializationOf(file_version.id, file.id)
    graph.wasInvalidatedBy(file_version.id, commit.id)
    return graph


def modification(graph, pkg, action):
    file, file_version, previous_versions = action
    author, commit = pkg.author, pkg.commit
    graph.entity(*file)
    graph.entity(*file_version)
    graph.wasAttributedTo(file_version.id, author.id)
    graph.wasGeneratedBy(file_version.id, commit.id)
    graph.specializationOf(file_version.id, file.id)
    for version in previous_versions:
        graph.entity(*version)
        graph.used(commit.id, version.id)
        graph.wasDerivedFrom(file_version.id, version.id)
        graph.specializationOf(version.id, file.id)
    return graph


def resource_package_model(graph, packages):
    for pkg in packages:
        add_creation = {
            CommitCreationPackage:  add_commit_creation,
            ResourceCreationPackage: add_resource_creation,
        }[type(pkg.creation)]
        graph = add_creation(graph, pkg)
        graph = add_event_chain(graph, pkg)
    return graph


def add_commit_creation(graph, pkg):
    committer, commit, creation, resource, resource_version = pkg.creation
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


def add_resource_creation(graph, pkg):
    creator, creation, resource, resource_version = pkg.creation
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


def add_event_chain(graph, pkg):
    previous_event = previous_resource_version = None
    for chain_link in pkg.event_chain:
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
