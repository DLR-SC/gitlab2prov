import logging
import itertools
from typing import Iterator
from dataclasses import dataclass, field, InitVar

from github import Github
from github.Repository import Repository

from gitlab2prov.adapters.project_url import GithubProjectUrl
from gitlab2prov.adapters.hub.parser import GithubAnnotationParser
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import (
    Asset,
    User,
    Commit,
    Issue,
    MergeRequest,
    GitTag,
    Release,
)


log = logging.getLogger(__name__)


@dataclass
class GithubFetcher:
    token: InitVar[str]
    url: InitVar[str]

    parser: GithubAnnotationParser = GithubAnnotationParser()
    client: Github = field(init=False)
    repository: Repository = field(init=False)

    def __post_init__(self, token, url) -> None:
        self.client = Github(login_or_token=token, per_page=100)
        self.repository = self.client.get_repo(full_name_or_id=GithubProjectUrl(url).slug)
        log.warning(f"Remaining requests: {self.client.rate_limiting[0]}")

    def fetch_all(self) -> Iterator[Commit | Issue | MergeRequest | Release | GitTag]:
        yield from itertools.chain(
            self.fetch_commits(),
            self.fetch_issues(),
            self.fetch_mergerequests(),
            self.fetch_releases(),
            self.fetch_tags(),
        )

    def fetch_commits(self) -> Iterator[Commit]:
        for commit in self.repository.get_commits():
            raw_annotations = [
                *commit.get_statuses(),
                *commit.get_comments(),
                *(comment.get_reactions() for comment in commit.get_comments()),
            ]
            yield Commit(
                sha=commit.sha,
                url=commit.url,
                author=User(
                    commit.commit.author.name,
                    commit.commit.author.email,
                    prov_role=ProvRole.COMMIT_AUTHOR,
                ),
                platform="github",
                annotations=self.parser.parse(raw_annotations),
                authored_at=commit.commit.author.date,
                committed_at=commit.commit.committer.date,
            )

    def fetch_issues(self) -> Iterator[Issue]:
        for issue in self.repository.get_issues(state="all"):
            raw_annotations = [
                *issue.get_comments(),
                *issue.get_reactions(),
                *(comment.get_reactions() for comment in issue.get_comments()),
                *issue.get_events(),
                *issue.get_timeline(),
            ]
            yield Issue(
                id=issue.number,
                iid=issue.id,
                platform="github",
                title=issue.title,
                body=issue.body,
                url=issue.url,
                author=User(issue.user.name, issue.user.email, prov_role=ProvRole.ISSUE_AUTHOR),
                annotations=self.parser.parse(raw_annotations),
                created_at=issue.created_at,
                closed_at=issue.closed_at,
            )

    def fetch_mergerequests(self) -> Iterator[MergeRequest]:
        for pull in self.repository.get_pulls(state="all"):
            raw_annotations = []
            raw_annotations.extend(pull.get_comments())
            raw_annotations.extend(comment.get_reactions() for comment in pull.get_comments())
            raw_annotations.extend(pull.get_review_comments())
            raw_annotations.extend(
                comment.get_reactions() for comment in pull.get_review_comments()
            )
            raw_annotations.extend(pull.get_reviews())
            raw_annotations.extend(pull.as_issue().get_reactions())
            raw_annotations.extend(pull.as_issue().get_events())
            raw_annotations.extend(pull.as_issue().get_timeline())

            yield MergeRequest(
                id=pull.number,
                iid=pull.id,
                title=pull.title,
                body=pull.body,
                url=pull.url,
                platform="github",
                source_branch=pull.base.ref,
                target_branch=pull.head.ref,
                author=User(
                    name=pull.user.name,
                    email=pull.user.email,
                    prov_role=ProvRole.MERGE_REQUEST_AUTHOR,
                ),
                annotations=self.parser.parse(raw_annotations),
                created_at=pull.created_at,
                closed_at=pull.closed_at,
                merged_at=pull.merged_at,
            )

    def fetch_releases(self) -> Iterator[Release]:
        for release in self.repository.get_releases():
            yield Release(
                name=release.title,
                body=release.body,
                tag_name=release.tag_name,
                platform="github",
                author=User(
                    name=release.author.name,
                    email=release.author.email,
                    prov_role=ProvRole.RELEASE_AUTHOR,
                ),
                assets=[
                    Asset(url=asset.url, format=asset.content_type)
                    for asset in release.get_assets()
                ],
                evidences=[],
                created_at=release.created_at,
                released_at=release.published_at,
            )

    def fetch_tags(self) -> Iterator[GitTag]:
        for tag in self.repository.get_tags():
            yield GitTag(
                name=tag.name,
                sha=tag.commit.sha,
                message=tag.commit.commit.message,
                author=User(
                    name=tag.commit.author.name,
                    email=tag.commit.author.email,
                    prov_role=ProvRole.TAG_AUTHOR,
                ),
                created_at=tag.commit.commit.author.date,
            )
