import logging
from typing import Optional, TypeAlias, Union

from prov.model import ProvDocument, PROV_ROLE

from gitlab2prov.adapters import repository
from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ChangeType, ProvRole


Resource: TypeAlias = Union[objects.GitlabCommit, objects.Issue, objects.MergeRequest]


logger = logging.getLogger(__name__)


def git_commit_model(graph: ProvDocument, repo: repository.AbstractRepository):
    """Commit model implementation."""
    for commit in repo.list_all(objects.GitCommit):
        # retrieve all files touched in this commit
        files = repo.list_all(objects.FileRevision, commit_hexsha=commit.hexsha)
        # retrieve all parent commits
        parents = [
            repo.get(objects.GitCommit, hexsha=hexsha) for hexsha in commit.parents
        ]
        parents = [parent for parent in parents if parent]
        # add nodes and relations
        graph = add_commit(graph, commit)
        graph = add_parents(graph, commit, parents)
        graph = add_files(graph, commit, files)
    return graph


def add_commit(graph: ProvDocument, cmt: objects.GitCommit):
    """Add commit activity, author & committer agents and all relations between those elements."""
    author = graph.agent(*cmt.author)
    committer = graph.agent(*cmt.committer)
    commit = graph.activity(*cmt)
    commit.wasAssociatedWith(author, attributes=[(PROV_ROLE, cmt.author.prov_role)])
    commit.wasAssociatedWith(
        committer, attributes=[(PROV_ROLE, cmt.committer.prov_role)]
    )
    return graph


def add_parents(
    graph: ProvDocument, commit: objects.GitCommit, parents: list[objects.GitCommit]
):
    """Add commit and parent commit activities and a 'wasInformedBy' relation between the two."""
    commit = graph.activity(*commit)
    for p in parents:
        parent = graph.activity(*p)
        commit.wasInformedBy(parent)
    return graph


def add_files(
    graph: ProvDocument, commit: objects.GitCommit, files: list[objects.FileRevision]
):
    """Add the file change models based on the change type of each file version."""
    for fv in files:
        if fv.change_type == ChangeType.ADDED:
            graph = addition(graph, commit, fv)
        if fv.change_type == ChangeType.MODIFIED:
            graph = modification(graph, commit, fv)
        if fv.change_type == ChangeType.DELETED:
            graph = deletion(graph, commit, fv)
    return graph


def addition(graph: ProvDocument, commit: objects.GitCommit, fv: objects.FileRevision):
    """Add model for the addition of a new file in a commit."""
    author = graph.agent(*commit.author)
    commit = graph.acitivity(*commit)
    file = graph.entity(*fv.original)
    file_version = graph.entity(*fv)
    file.wasGeneratedBy(
        commit,
        time=commit.prov_start,
        attributes=[(PROV_ROLE, ProvRole.File)],
    )
    file_version.wasGeneratedBy(
        commit,
        time=commit.prov_start,
        attributes=[(PROV_ROLE, ProvRole.FileRevisionAtPointOfAddition)],
    )
    file.wasAttributedTo(author)
    file_version.wasAttributedTo(author)
    file_version.specializationOf(file)
    return graph


def modification(
    graph: ProvDocument, commit_: objects.GitCommit, fv: objects.FileRevision
):
    author = graph.agent(*commit_.author)
    commit = graph.activity(*commit_)
    file = graph.entity(*fv.original)
    file_version = graph.entity(*fv)
    prev_version = graph.entity(*fv.previous)
    prev_version.specializationOf(file)
    file_version.wasAttributedTo(author)
    file_version.wasGeneratedBy(
        commit,
        time=commit_.prov_start,
        attributes=[(PROV_ROLE, ProvRole.FileRevisionAfterModification)],
    )
    file_version.specializationOf(file)
    file_version.wasRevisionOf(prev_version)
    commit.used(
        prev_version,
        time=commit.prov_start,
        attributes=[(PROV_ROLE, ProvRole.FileRevisionToBeModified)],
    )
    return graph


def deletion(graph: ProvDocument, cmt: objects.GitCommit, fv: objects.FileRevision):
    commit = graph.activity(*cmt)
    file = graph.entity(*fv.original)
    file_version = graph.entity(*fv)
    file_version.specializationOf(file)
    file_version.wasInvalidatedBy(
        commit,
        time=cmt.prov_start,
        attributes=[(PROV_ROLE, ProvRole.FileRevisionAtPointOfDeletion)],
    )
    return graph


def gitlab_commit_model(graph: ProvDocument, repo):
    for gitlab_commit in repo.list_all(objects.GitlabCommit):
        # retrieve corresponding git commit
        # could be none
        git_commit = repo.get(objects.GitCommit, hexsha=gitlab_commit.hexsha)
        # add nodes & relations
        graph = add_commit_creation(graph, gitlab_commit, git_commit)
        graph = add_annotations(graph, gitlab_commit)
    return graph


def gitlab_issue_model(graph: ProvDocument, repo):
    for issue in repo.list_all(objects.Issue):
        graph = add_resource_creation(graph, issue)
        graph = add_annotations(graph, issue)
    return graph


def gitlab_merge_request_model(graph: ProvDocument, repo):
    for merge_request in repo.list_all(objects.MergeRequest):
        graph = add_resource_creation(graph, merge_request)
        graph = add_annotations(graph, merge_request)
    return graph


def add_commit_creation(
    graph: ProvDocument,
    rsrc: objects.GitlabCommit,
    git_commit: Optional[objects.Creation],
):
    creation = graph.activity(*rsrc.creation)
    resource = graph.entity(*rsrc)
    resource_version = graph.entity(*rsrc.first_version)
    resource.wasGeneratedBy(
        creation,
        time=rsrc.creation.prov_start,
        attributes=[(PROV_ROLE, ProvRole.Resource)],
    )
    resource_version.wasGeneratedBy(
        creation,
        time=rsrc.creation.prov_start,
        attributes=[(PROV_ROLE, ProvRole.ResourceVersionAtPointOfCreation)],
    )
    resource_version.specializationOf(resource)
    committer = graph.agent(*rsrc.author)
    creation.wasAssociatedWith(
        committer, attributes=[(PROV_ROLE, ProvRole.GitlabCommitAuthor)]
    )
    resource.wasAttributedTo(committer)
    resource_version.wasAttributedTo(committer)
    if git_commit:
        commit = graph.activity(*git_commit)
        commit.wasAssociatedWith(
            committer, attributes=[(PROV_ROLE, ProvRole.Committer)]
        )
        creation.wasInformedBy(commit)
    return graph


def add_resource_creation(graph: ProvDocument, rsrc: Resource):
    resource = graph.entity(*rsrc)
    resource_version = graph.entity(*rsrc.first_version)
    creation = graph.activity(*rsrc.creation)
    author = graph.agent(*rsrc.author)
    creation.wasAssociatedWith(author, attributes=[(PROV_ROLE, rsrc.author.prov_role)])
    resource.wasAttributedTo(author)
    resource_version.wasAttributedTo(author)
    resource_version.specializationOf(resource)
    resource.wasGeneratedBy(
        creation,
        time=rsrc.creation.prov_start,
        attributes=[(PROV_ROLE, ProvRole.Resource)],
    )
    resource_version.wasGeneratedBy(
        creation,
        time=rsrc.creation.prov_start,
        attributes=[(PROV_ROLE, ProvRole.ResourceVersionAtPointOfCreation)],
    )
    return graph


def add_annotations(graph: ProvDocument, rsrc: Resource):
    resource = graph.entity(*rsrc)
    creation = graph.activity(*rsrc.creation)
    first_version = graph.entity(*rsrc.first_version)

    previous_annotation = creation
    previous_annotated_version = first_version

    for annot, version in zip(rsrc.annotations, rsrc.annotated_versions):
        annotation = graph.activity(*annot)
        annotated_version = graph.entity(*version)
        annotator = graph.agent(*annot.annotator)
        annotation.wasAssociatedWith(
            annotator, attributes=[(PROV_ROLE, annot.annotator.prov_role)]
        )
        annotation.wasInformedBy(previous_annotation)
        annotation.used(
            previous_annotated_version,
            time=annot.prov_start,
            attributes=[(PROV_ROLE, ProvRole.ResourceVersionToBeAnnotated)],
        )
        annotated_version.wasAttributedTo(annotator)
        annotated_version.wasGeneratedBy(
            annotation,
            time=annot.prov_start,
            attributes=[(PROV_ROLE, ProvRole.ResourceVersionAfterAnnotation)],
        )
        annotated_version.specializationOf(resource)
        annotated_version.wasDerivedFrom(previous_annotated_version)
        # update previous annotation
        previous_annotation = annotation
        # update previous annotated version
        previous_annotated_version = annotated_version
    return graph


def gitlab_release_tag_model(graph: ProvDocument, repo):
    for tag in repo.list_all(objects.Tag):
        release = repo.get(objects.Release, tag_name=tag.name)
        commit = repo.get(objects.GitlabCommit, hexsha=tag.hexsha)
        graph = add_release_and_tag(graph, release, tag)
        graph = add_tag_and_commit(graph, tag, commit)
    return graph


def add_release_and_tag(graph: ProvDocument, rls: objects.Release, tag: objects.Tag):
    tag = graph.entity(*tag)
    if not rls:
        return graph
    release = graph.entity(*rls)
    creation = graph.activity(*rls.creation)
    release.wasGeneratedBy(
        creation,
        time=rls.creation.prov_start,
        attributes=[(PROV_ROLE, ProvRole.Release)],
    )
    if rls.author:
        author = graph.agent(*rls.author)
        release.wasAttributedTo(author)
        creation.wasAssociatedWith(
            author, attributes=[(PROV_ROLE, rls.author.prov_role)]
        )
    for asset in rls.assets:
        asset = graph.entity(*asset)
        asset.hadMember(release)
    for evidence in rls.evidences:
        evidence = graph.entity(*evidence)
        evidence.hadMember(release)
    tag.hadMember(release)
    return graph


def add_tag_and_commit(graph: ProvDocument, tag_: objects.Tag, cmt: objects.GitCommit):
    creation = graph.activity(*tag_.creation)
    author = graph.agent(*tag_.author)
    tag = graph.entity(*tag_)
    tag.wasGeneratedBy(creation)
    tag.wasAttributedTo(author)
    creation.wasAssociatedWith(author, attributes=[(PROV_ROLE, tag_.author.prov_role)])
    if cmt:
        creation = graph.activity(*cmt.creation)
        author = graph.agent(*cmt.author)
        commit = graph.entity(*cmt)
        commit.wasGeneratedBy(
            creation,
            time=cmt.creation.prov_start,
            attributes=[(PROV_ROLE, ProvRole.GitCommit)],
        )
        commit.wasAttributedTo(author)
        creation.wasAssociatedWith(
            author, attributes=[(PROV_ROLE, cmt.author.prov_role)]
        )
        commit.hadMember(tag)
    return graph


MODELS = [
    git_commit_model,
    gitlab_commit_model,
    gitlab_issue_model,
    gitlab_merge_request_model,
    gitlab_release_tag_model,
]
