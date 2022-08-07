from dataclasses import dataclass, field
import logging
from typing import Iterator

from gitlab2prov.adapters.fetch.utils import gitlab_url, project_slug
from gitlab2prov.adapters.fetch.parse import parse_annotations
from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvRole

from gitlab import Gitlab
from gitlab.v4.objects import Project
from gitlab.exceptions import GitlabListError


log = logging.getLogger(__name__)


@dataclass
class GitlabFetcher:
    project_url: str
    private_token: str
    project: Project | None = field(init=False, default=None)

    def do_login(self) -> None:
        gl = Gitlab(url=gitlab_url(self.project_url), private_token=self.private_token)
        self.project = gl.projects.get(project_slug(self.project_url))

    def fetch_gitlab(self) -> Iterator[objects.ProvInterface]:
        yield from extract_commits(self.project)
        yield from extract_issues(self.project)
        yield from extract_mergerequests(self.project)
        yield from extract_releases(self.project)
        yield from extract_tags(self.project)


def on_gitlab_list_error(func):
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GitlabListError as e:
            msg = f"{func.__module__}.{func.__name__}: {type(e)} due to {e.response_code} HTTP Error."
            log.info(msg)

    return wrapped


def get_commit_author(commit):
    return objects.User(
        name=commit.committer_name,
        email=commit.committer_email,
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.AUTHOR_GITLAB_COMMIT,
    )


def get_tag_author(tag):
    return objects.User(
        name=tag.commit.get("author_name"),
        email=tag.commit.get("author_email"),
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.AUTHOR_TAG,
    )


def get_resource_author(resource, role: ProvRole):
    if not hasattr(resource, "author"):
        return None
    return objects.User(
        name=resource.author.get("name"),
        email=resource.author.get("email"),
        gitlab_username=resource.author.get("username"),
        gitlab_id=resource.author.get("id"),
        prov_role=role,
    )


def get_assets(release):
    return [
        objects.Asset(url=asset.get("url"), format=asset.get("format"))
        for asset in release.assets.get("sources", [])
    ]


def get_evidences(release):
    return [
        objects.Evidence(
            hexsha=evidence.get("sha"),
            url=evidence.get("filepath"),
            collected_at=evidence.get("collected_at"),
        )
        for evidence in release.evidences
    ]


@on_gitlab_list_error
def extract_commits(project):
    for commit in project.commits.list(all=True):
        parseables = {
            *commit.comments.list(all=True, system=False),
            *commit.comments.list(all=True, system=True),
        }
        yield objects.GitlabCommit(
            hexsha=commit.id,
            url=commit.web_url,
            author=get_commit_author(commit),
            annotations=parse_annotations(parseables),
            authored_at=commit.authored_date,
            committed_at=commit.committed_date,
        )


@on_gitlab_list_error
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
        yield objects.Issue(
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


@on_gitlab_list_error
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
        yield objects.MergeRequest(
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


@on_gitlab_list_error
def extract_releases(project):
    for release in project.releases.list(all=True):
        yield objects.Release(
            name=release.name,
            description=release.description,
            tag_name=release.tag_name,
            author=get_resource_author(release, ProvRole.AUTHOR_RELEASE),
            assets=get_assets(release),
            evidences=get_evidences(release),
            created_at=release.created_at,
            released_at=release.released_at,
        )


@on_gitlab_list_error
def extract_tags(project):
    for tag in project.tags.list(all=True):
        yield objects.Tag(
            name=tag.name,
            hexsha=tag.target,
            message=tag.message,
            author=get_tag_author(tag),
            created_at=tag.commit.get("created_at"),
        )
