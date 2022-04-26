from abc import ABC, abstractmethod
from dataclasses import dataclass

from gitlab.v4.objects import Project

from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.adapters.miners.annotation_parsing import parse_annotations
from gitlab2prov.domain.objects import (
    Asset,
    Evidence,
    GitlabCommit,
    Issue,
    MergeRequest,
    Release,
    User,
    Tag,
)


@dataclass
class AbstractMiner(ABC):
    @abstractmethod
    def mine(self):
        raise NotImplementedError


@dataclass
class GitlabProjectMiner(AbstractMiner):
    project: Project

    def mine(self):
        yield from extract_commits(self.project)
        yield from extract_issues(self.project)
        yield from extract_mergerequests(self.project)
        yield from extract_releases(self.project)
        yield from extract_tags(self.project)


def get_commit_author(commit):
    return User(
        name=commit.committer_name,
        email=commit.committer_email,
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.AUTHOR_GITLAB_COMMIT,
    )


def get_tag_author(tag):
    return User(
        name=tag.commit.get("author_name"),
        email=tag.commit.get("author_email"),
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.AUTHOR_TAG,
    )


def get_resource_author(resource, role: ProvRole):
    if not hasattr(resource, "author"):
        return None
    return User(
        name=resource.author.get("name"),
        email=resource.author.get("email"),
        gitlab_username=resource.author.get("username"),
        gitlab_id=resource.author.get("id"),
        prov_role=role,
    )


def get_assets(release):
    return [
        Asset(url=asset.get("url"), format=asset.get("format"))
        for asset in release.assets.get("sources", [])
    ]


def get_evidences(release):
    return [
        Evidence(
            hexsha=evidence.get("sha"),
            url=evidence.get("filepath"),
            collected_at=evidence.get("collected_at"),
        )
        for evidence in release.evidences
    ]


def extract_commits(project):
    for commit in project.commits.list(all=True):
        parseables = {
            *commit.comments.list(all=True, system=False),
            *commit.comments.list(all=True, system=True),
        }
        yield GitlabCommit(
            hexsha=commit.id,
            url=commit.web_url,
            author=get_commit_author(commit),
            annotations=parse_annotations(parseables),
            authored_at=commit.authored_date,
            committed_at=commit.committed_date,
        )


def extract_issues(project):
    for issue in project.issues.list(all=True):
        parseables = {
            *issue.notes.list(all=True, system=False),
            *issue.notes.list(all=True, system=True),
            *issue.awardemojis.list(all=True),
            *issue.resourcelabelevents.list(all=True),
            *(
                award
                for note in issue.notes.list(all=True)
                for award in note.awardemojis.list(all=True)
            ),
        }
        yield Issue(
            id=issue.id,
            iid=issue.iid,
            title=issue.title,
            description=issue.description,
            url=issue.web_url,
            author=get_resource_author(issue, ProvRole.AUTHOR_ISSUE),
            annotations=parse_annotations(parseables),
            created_at=issue.created_at,
            closed_at=issue.closed_at,
        )


def extract_mergerequests(project):
    for mergerequest in project.mergerequests.list(all=True):
        parseables = {
            *mergerequest.notes.list(all=True, system=False),
            *mergerequest.notes.list(all=True, system=True),
            *mergerequest.awardemojis.list(all=True),
            *mergerequest.resourcelabelevents.list(all=True),
            *(
                award
                for note in mergerequest.notes.list(all=True)
                for award in note.awardemojis.list(all=True)
            ),
        }
        yield MergeRequest(
            id=mergerequest.id,
            iid=mergerequest.iid,
            title=mergerequest.title,
            description=mergerequest.description,
            url=mergerequest.web_url,
            source_branch=mergerequest.source_branch,
            target_branch=mergerequest.target_branch,
            author=get_resource_author(mergerequest, ProvRole.AUTHOR_MERGE_REQUEST),
            annotations=parse_annotations(parseables),
            created_at=mergerequest.created_at,
            closed_at=mergerequest.closed_at,
            merged_at=mergerequest.merged_at,
            first_deployed_to_production_at=getattr(
                mergerequest, "first_deployed_to_production_at", None
            ),
        )


def extract_releases(project):
    for release in project.releases.list(all=True):
        yield Release(
            name=release.name,
            description=release.description,
            tag_name=release.tag_name,
            author=get_resource_author(release, ProvRole.AUTHOR_RELEASE),
            assets=get_assets(release),
            evidences=get_evidences(release),
            created_at=release.created_at,
            released_at=release.released_at,
        )


def extract_tags(project):
    for tag in project.tags.list(all=True):
        yield Tag(
            name=tag.name,
            hexsha=tag.target,
            message=tag.message,
            author=get_tag_author(tag),
            created_at=tag.commit.get("created_at"),
        )
