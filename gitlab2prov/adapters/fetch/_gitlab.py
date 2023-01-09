import logging
import itertools

from dataclasses import dataclass, field, InitVar
from typing import Iterator

from gitlab import Gitlab
from gitlab.exceptions import GitlabListError

from gitlab2prov.adapters.fetch.annotations import parse_annotations
from gitlab2prov.adapters.fetch.utils import instance_url, project_slug
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import (
    Asset,
    Evidence,
    Commit,
    Issue,
    MergeRequest,
    Release,
    GitTag,
    User,
    GitTag,
)


log = logging.getLogger(__name__)


@dataclass
class GitlabFetcher:
    private_token: InitVar[str]
    url: InitVar[str] = "https://gitlab.com"

    client: Gitlab = field(init=False)
    project: Gitlab = field(init=False)

    def __post_init__(self, private_token, url) -> None:
        self.client = Gitlab(instance_url(url), private_token=private_token)
        self.project = self.client.projects.get(project_slug(url))

    def log_list_err(self, log: logging.Logger, err: GitlabListError, cls: str) -> None:
        log.error(f"failed to fetch {cls} from {instance_url(self.project)}")
        log.error(f"error: {err}")

    def fetch_all(self) -> Iterator[Commit | Issue | MergeRequest | Release | GitTag]:
        yield from itertools.chain(
            self.fetch_commits(),
            self.fetch_issues(),
            self.fetch_mergerequests(),
            self.fetch_releases(),
            self.fetch_tags(),
        )

    def fetch_commits(self) -> Iterator[Commit]:
        try:
            for commit in self.project.commits.list(all=True, per_page=100):
                yield Commit(
                    sha=commit.id,
                    url=commit.web_url,
                    platform="gitlab",
                    author=User(
                        commit.author_name, commit.author_email, prov_role=ProvRole.COMMIT_AUTHOR
                    ),
                    annotations=parse_annotations(
                        [
                            *commit.comments.list(all=True, system=False),
                            *commit.comments.list(all=True, system=True),
                        ]
                    ),
                    authored_at=commit.authored_date,
                    committed_at=commit.committed_date,
                )
        except GitlabListError as err:
            self.log_list_err(log, err, "commits")

    def fetch_issues(self, state="all") -> Iterator[Issue]:
        try:
            for issue in self.project.issues.list(all=True, state=state, per_page=100):
                yield Issue(
                    id=issue.id,
                    iid=issue.iid,
                    platform="gitlab",
                    title=issue.title,
                    body=issue.description,
                    url=issue.web_url,
                    author=User(
                        issue.author.get("name"),
                        issue.author.get("email"),
                        gitlab_username=issue.author.get("username"),
                        gitlab_id=issue.author.get("id"),
                        prov_role=ProvRole.ISSUE_AUTHOR,
                    ),
                    annotations=parse_annotations(
                        [
                            *issue.notes.list(all=True, system=False),
                            *issue.notes.list(all=True, system=True),
                            *issue.awardemojis.list(all=True),
                            *issue.resourcelabelevents.list(all=True),
                            *(
                                award
                                for note in issue.notes.list(all=True)
                                for award in note.awardemojis.list(all=True)
                            ),
                        ]
                    ),
                    created_at=issue.created_at,
                    closed_at=issue.closed_at,
                )
        except GitlabListError as err:
            self.log_list_err(log, err, "issues")

    def fetch_mergerequests(self, state="all") -> Iterator[MergeRequest]:
        try:
            for merge in self.project.mergerequests.list(all=True, state=state, per_page=100):
                yield MergeRequest(
                    id=merge.id,
                    iid=merge.iid,
                    title=merge.title,
                    body=merge.description,
                    url=merge.web_url,
                    platform="gitlab",
                    source_branch=merge.source_branch,
                    target_branch=merge.target_branch,
                    author=User(
                        merge.author.get("name"),
                        merge.author.get("email"),
                        gitlab_username=merge.author.get("username"),
                        gitlab_id=merge.author.get("id"),
                        prov_role=ProvRole.MERGE_REQUEST_AUTHOR,
                    ),
                    annotations=parse_annotations(
                        (
                            *merge.notes.list(all=True, system=False),
                            *merge.notes.list(all=True, system=True),
                            *merge.awardemojis.list(all=True),
                            *merge.resourcelabelevents.list(all=True),
                            *(
                                award
                                for note in merge.notes.list(all=True)
                                for award in note.awardemojis.list(all=True)
                            ),
                        )
                    ),
                    created_at=merge.created_at,
                    closed_at=merge.closed_at,
                    merged_at=merge.merged_at,
                    first_deployed_to_production_at=getattr(merge, "first_deployed_to_production_at", None),
                )
        except GitlabListError as err:
            self.log_list_err(log, err, "merge requests")

    def fetch_releases(self) -> Iterator[Release]:
        try:
            for release in self.project.releases.list(all=True, per_page=100):
                yield Release(
                    name=release.name,
                    body=release.description,
                    tag_name=release.tag_name,
                    author=User(
                        name=release.author.get("name"),
                        email=release.author.get("email"),
                        gitlab_username=release.author.get("username"),
                        gitlab_id=release.author.get("id"),
                        prov_role=ProvRole.RELEASE_AUTHOR,
                    ),
                    assets=[
                        Asset(url=asset.get("url"), format=asset.get("format"))
                        for asset in release.assets.get("sources", [])
                    ],
                    evidences=[
                        Evidence(
                            sha=evidence.get("sha"),
                            url=evidence.get("filepath"),
                            collected_at=evidence.get("collected_at"),
                        )
                        for evidence in release.evidences
                    ],
                    created_at=release.created_at,
                    released_at=release.released_at,
                )
        except GitlabListError as err:
            self.log_list_err(log, err, "releases")

    def fetch_tags(self) -> Iterator[GitTag]:
        try:
            for tag in self.project.tags.list(all=True, per_page=100):
                yield GitTag(
                    name=tag.name,
                    sha=tag.target,
                    message=tag.message,
                    author=User(
                        name=tag.commit.get("author_name"),
                        email=tag.commit.get("author_email"),
                        prov_role=ProvRole.TAG_AUTHOR,
                    ),
                    created_at=tag.commit.get("created_at"),
                )
        except GitlabListError as err:
            self.log_list_err(log, err, "tags")
