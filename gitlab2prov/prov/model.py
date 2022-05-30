from typing import Optional, Union

from prov.model import ProvDocument, PROV_ROLE

from gitlab2prov.prov.operations import graph_factory
from gitlab2prov.adapters.repository import AbstractRepository
from gitlab2prov.domain.constants import ChangeType, ProvRole
from gitlab2prov.domain.objects import (
    FileRevision,
    GitCommit,
    GitlabCommit,
    Issue,
    MergeRequest,
    Release,
    Tag,
)


Resource = Union[GitlabCommit, Issue, MergeRequest]


def git_commit_model(
    resources: AbstractRepository, graph: ProvDocument = graph_factory()
):
    """Commit model implementation."""
    for commit in resources.list_all(GitCommit):
        file_revisions = resources.list_all(FileRevision, committed_in=commit.hexsha)
        parents = [resources.get(GitCommit, hexsha=hexsha) for hexsha in commit.parents]
        parents = [parent for parent in parents if parent is not None]
        for rev in file_revisions:
            model = choose_rev_model(rev)
            if model is None:
                continue
            graph.update(model(commit, parents, rev))
    return graph


def choose_rev_model(rev: FileRevision):
    """Add the file change models based on the change type of each file version."""
    if rev.change_type == ChangeType.ADDED:
        return addition
    if (
        rev.change_type == ChangeType.MODIFIED
        or rev.change_type == ChangeType.RENAMED
        or rev.change_type == ChangeType.COPIED
        or rev.change_type == ChangeType.CHANGED
    ):
        return modification
    if rev.change_type == ChangeType.DELETED:
        return deletion
    return None


def addition(
    commit: GitCommit,
    parents: list[GitCommit],
    rev: FileRevision,
    graph: ProvDocument = graph_factory(),
):
    """Add model for the addition of a new file in a commit."""
    c = graph.activity(*commit)
    at = graph.agent(*commit.author)
    ct = graph.agent(*commit.committer)

    c.wasAssociatedWith(at, None, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])
    c.wasAssociatedWith(ct, None, [(PROV_ROLE, list(ct.get_attribute(PROV_ROLE))[0])])

    for parent in parents:
        graph.activity(*commit).wasInformedBy(graph.activity(*parent))

    f = graph.entity(*rev.original)
    f.wasAttributedTo(at)
    f.wasGeneratedBy(c, c.get_startTime(), [(PROV_ROLE, ProvRole.FILE)])

    rev = graph.entity(*rev)
    rev.wasAttributedTo(at)
    rev.specializationOf(f)
    rev.wasGeneratedBy(
        c, c.get_startTime(), [(PROV_ROLE, ProvRole.FILE_REVISION_AT_POINT_OF_ADDITION)]
    )
    return graph


def modification(
    commit: GitCommit,
    parents: list[GitCommit],
    fv: FileRevision,
    graph: ProvDocument = graph_factory(),
):
    c = graph.activity(*commit)
    at = graph.agent(*commit.author)
    ct = graph.agent(*commit.committer)

    c.wasAssociatedWith(at, None, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])
    c.wasAssociatedWith(ct, None, [(PROV_ROLE, list(ct.get_attribute(PROV_ROLE))[0])])

    for parent in parents:
        graph.activity(*commit).wasInformedBy(graph.activity(*parent))

    f = graph.entity(*fv.original)
    prev = graph.entity(*fv.previous)
    prev.specializationOf(f)
    rev = graph.entity(*fv)
    rev.wasAttributedTo(at)
    rev.specializationOf(f)
    graph.wasRevisionOf(
        rev, prev
    )  # NOTE: rev.wasRevisionOf(prev) is not impl in prov pkg
    rev.wasGeneratedBy(
        c,
        c.get_startTime(),
        [(PROV_ROLE, ProvRole.FILE_REVISION_AFTER_MODIFICATION)],
    )
    c.used(
        prev,
        c.get_startTime(),
        [(PROV_ROLE, ProvRole.FILE_REVISION_TO_BE_MODIFIED)],
    )
    return graph


def deletion(
    commit: GitCommit,
    parents: list[GitCommit],
    fv: FileRevision,
    graph: ProvDocument = graph_factory(),
):
    c = graph.activity(*commit)
    at = graph.agent(*commit.author)
    ct = graph.agent(*commit.committer)

    c.wasAssociatedWith(at, None, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])
    c.wasAssociatedWith(ct, None, [(PROV_ROLE, list(ct.get_attribute(PROV_ROLE))[0])])

    for parent in parents:
        graph.activity(*commit).wasInformedBy(graph.activity(*parent))

    f = graph.entity(*fv.original)
    rev = graph.entity(*fv)
    rev.specializationOf(f)
    rev.wasInvalidatedBy(
        c,
        c.get_startTime(),
        [(PROV_ROLE, ProvRole.FILE_REVISION_AT_POINT_OF_DELETION)],
    )
    return graph


def gitlab_commit_model(resources, graph: ProvDocument = graph_factory()):
    for gitlab_commit in resources.list_all(GitlabCommit):
        git_commit = resources.get(GitCommit, hexsha=gitlab_commit.hexsha)
        graph.update(commit_creation(gitlab_commit, git_commit))
        graph.update(annotation_chain(gitlab_commit))
        return graph
    return graph


def gitlab_issue_model(resources, graph: ProvDocument = graph_factory()):
    for issue in resources.list_all(Issue):
        graph.update(resource_creation(issue))
        graph.update(annotation_chain(issue))
    return graph


def gitlab_merge_request_model(resources, graph: ProvDocument = graph_factory()):
    for merge_request in resources.list_all(MergeRequest):
        graph.update(resource_creation(merge_request))
        graph.update(annotation_chain(merge_request))
    return graph


def commit_creation(
    gitlab_commit: GitlabCommit,
    git_commit: Optional[GitCommit],
    graph: ProvDocument = graph_factory(),
):
    resource = graph.entity(*gitlab_commit)
    creation = graph.activity(*gitlab_commit.creation)
    first_version = graph.entity(*gitlab_commit.first_version)
    author = graph.agent(*gitlab_commit.author)

    resource.wasAttributedTo(author)
    creation.wasAssociatedWith(
        author, None, [(PROV_ROLE, ProvRole.AUTHOR_GITLAB_COMMIT)]
    )
    resource.wasGeneratedBy(
        creation, creation.get_startTime(), [(PROV_ROLE, ProvRole.RESOURCE)]
    )
    first_version.wasGeneratedBy(
        creation,
        creation.get_startTime(),
        [(PROV_ROLE, ProvRole.RESOURCE_VERSION_AT_POINT_OF_CREATION)],
    )
    first_version.specializationOf(resource)
    first_version.wasAttributedTo(author)

    if git_commit is None:
        return graph

    commit = graph.activity(*git_commit)
    committer = graph.agent(*git_commit.committer)
    commit.wasAssociatedWith(committer, None, [(PROV_ROLE, ProvRole.COMMITTER)])
    creation.wasInformedBy(commit)

    return graph


def resource_creation(resource: Resource, graph: ProvDocument = graph_factory()):
    r = graph.entity(*resource)
    c = graph.activity(*resource.creation)
    rv = graph.entity(*resource.first_version)
    at = graph.agent(*resource.author)

    c.wasAssociatedWith(at, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])

    r.wasAttributedTo(at)
    rv.wasAttributedTo(at)
    rv.specializationOf(r)
    r.wasGeneratedBy(
        c,
        c.get_startTime(),
        [(PROV_ROLE, ProvRole.RESOURCE)],
    )
    rv.wasGeneratedBy(
        c,
        c.get_startTime(),
        [(PROV_ROLE, ProvRole.RESOURCE_VERSION_AT_POINT_OF_CREATION)],
    )
    return graph


def annotation_chain(resource, graph=graph_factory()):
    r = graph.entity(*resource)
    c = graph.activity(*resource.creation)
    fv = graph.entity(*resource.first_version)

    prev_annot = c
    prev_annot_ver = fv

    for annotation, annotated_version in zip(
        resource.annotations, resource.annotated_versions
    ):
        annot = graph.activity(*annotation)
        annot_ver = graph.entity(*annotated_version)
        annotator = graph.agent(*annotation.annotator)

        annot.wasInformedBy(prev_annot)
        annot_ver.wasDerivedFrom(prev_annot_ver)
        annot_ver.wasAttributedTo(annotator)
        annot_ver.specializationOf(r)

        annot.wasAssociatedWith(
            annotator, None, [(PROV_ROLE, list(annotator.get_attribute(PROV_ROLE))[0])]
        )

        annot.used(
            prev_annot_ver,
            annot.get_startTime(),
            [(PROV_ROLE, list(annotator.get_attribute(PROV_ROLE))[0])],
        )
        annot_ver.wasGeneratedBy(
            annot,
            annot.get_startTime(),
            [(PROV_ROLE, ProvRole.RESOURCE_VERSION_AFTER_ANNOTATION)],
        )
        prev_annot = annot
        prev_annot_ver = annot_ver
    return graph


def gitlab_release_tag_model(resources, graph: ProvDocument = graph_factory()):
    for tag in resources.list_all(Tag):
        release = resources.get(Release, tag_name=tag.name)
        commit = resources.get(GitlabCommit, hexsha=tag.hexsha)
        graph.update(release_and_tag(release, tag))
        graph.update(tag_and_commit(tag, commit))
    return graph


def release_and_tag(
    release: Optional[Release], tag: Tag, graph: ProvDocument = graph_factory()
):
    t = graph.collection(*tag)

    if release is None:
        return graph

    r = graph.collection(*release)
    c = graph.activity(*release.creation)
    t.hadMember(r)
    r.wasGeneratedBy(c, c.get_startTime(), [(PROV_ROLE, ProvRole.RELEASE)])
    for asset in release.assets:
        graph.entity(*asset).hadMember(graph.entity(*release))
    for evidence in release.evidences:
        graph.entity(*evidence).hadMember(graph.entity(*release))

    if release.author is None:
        return graph

    at = graph.agent(*release.author)
    r.wasAttributedTo(at)
    c.wasAssociatedWith(at, None, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])

    return graph


def tag_and_commit(
    tag: Tag, commit: Optional[GitlabCommit], graph: ProvDocument = graph_factory()
):
    t = graph.collection(*tag)
    tc = graph.activity(*tag.creation)
    at = graph.agent(*tag.author)
    t.wasAttributedTo(at)
    t.wasGeneratedBy(tc, tc.get_startTime(), [(PROV_ROLE, ProvRole.TAG)])
    tc.wasAssociatedWith(at, None, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])

    if commit is None:
        return graph

    cmt = graph.entity(*commit)
    cc = graph.activity(*commit.creation)
    at = graph.agent(*commit.author)
    cmt.hadMember(t)
    cmt.wasAttributedTo(at)
    cmt.wasGeneratedBy(cc, cc.get_startTime(), [(PROV_ROLE, ProvRole.GIT_COMMIT)])
    cc.wasAssociatedWith(at, None, [(PROV_ROLE, list(at.get_attribute(PROV_ROLE))[0])])

    return graph


MODELS = [
    git_commit_model,
    gitlab_commit_model,
    gitlab_issue_model,
    gitlab_merge_request_model,
    gitlab_release_tag_model,
]
