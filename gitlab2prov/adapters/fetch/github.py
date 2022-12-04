import logging

from dataclasses import dataclass, field

import github

from gitlab2prov.adapters.fetch.annotations import parse_annotations
from gitlab2prov.adapters.fetch.utils import project_slug
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import (
    Asset,
    GithubCommit,
    Release,
    Tag,
    User,
    GithubCommit,
    GithubIssue,
    GithubPullRequest,
)


log = logging.getLogger(__name__)


@dataclass
class GithubFetcher:
    repository: github.Repository.Repository = field(init=False)

    def do_login(self, url: str, token: str) -> None:
        gh = github.Github(login_or_token=token, per_page=100)
        log.warn(f"Remaining requests: {gh.rate_limiting[0]}")
        self.repository = gh.get_repo(full_name_or_id=project_slug(url))

    def do_fetch(self):
        yield from self.fetch_commits()
        yield from self.fetch_issues()
        yield from self.fetch_pullrequests()
        yield from self.fetch_releases()
        yield from self.fetch_tags()

    def fetch_commits(self):
        """
        commits can have statuses
        https://docs.github.com/en/rest/reference/repos#list-commit-statuses-for-a-reference
        commits can have checks
        https://docs.github.com/en/rest/reference/checks#list-check-runs-for-a-git-reference
        commits can have comments
        https://docs.github.com/en/rest/reference/repos#list-commit-comments-for-a-repository
        which users can add reactions to (emoji)
        https://docs.github.com/en/rest/reference/reactions#list-reactions-for-a-commit-comment

        annotations should be parsed from anything that adds additional information to a commit
        - commit statuses
        - commit checks
        - commit comments
        - commit reactions
        """
        for commit in self.repository.get_commits():

            parseables = []
            parseables.extend(commit.get_statuses())
            parseables.extend(commit.get_comments())
            parseables.extend(comment.get_reactions() for comment in commit.get_comments())

            yield self.commit2ir(commit, raw_annotations=parseables)

    @staticmethod
    def commit2ir(commit, raw_annotations):
        return GithubCommit(
            hexsha=commit.sha,
            url=commit.url,
            author=User(
                name=commit.commit.author.name,
                email=commit.commit.author.email,
                prov_role=ProvRole.AUTHOR_GITHUB_COMMIT,
            ),
            annotations=[],
            # parse_annotations(parseables),
            authored_at=commit.commit.author.date,
            committed_at=commit.commit.committer.date,
        )

    def fetch_issues(self):
        """
        issues can have comments
        https://docs.github.com/en/rest/reference/issues#list-issue-comments
        which users can add reactions to (emoji)
        https://docs.github.com/en/rest/reference/reactions#list-reactions-for-an-issue-comment
        users can add reactions to issues
        https://docs.github.com/en/rest/reference/reactions#list-reactions-for-an-issue
        issues can have labels
        https://docs.github.com/en/rest/reference/issues#list-labels-for-an-issue
        issues can have events
        https://docs.github.com/en/rest/reference/issues#list-issue-events
        issues can have a timeline
        https://docs.github.com/en/rest/reference/issues#list-timeline-events-for-an-issue
        issues can have milestones
        https://docs.github.com/en/rest/reference/issues#list-milestones-for-an-issue

        annotations should be parsed from anything that adds additional information to an issue
        - issue comments
        - issue reactions
        - issue comment reactions
        - issue events
        - issue labels
        - issue milestones

        TODO: do events overlap with information gained from other resources?
        """
        for issue in self.repository.get_issues(state="all"):

            parseables = []
            parseables.extend(issue.get_comments())
            parseables.extend(comment.get_reactions() for comment in issue.get_comments())
            parseables.extend(issue.get_labels())
            parseables.extend(issue.get_events())
            parseables.extend(issue.get_timeline())

            yield self.issue2ir(issue, raw_annotations=parseables)

    @staticmethod
    def issue2ir(issue, raw_annotations):
        return GithubIssue(
            number=issue.number,
            id=issue.id,
            title=issue.title,
            body=issue.body,
            url=issue.url,
            author=User(
                name=issue.user.name, email=issue.user.email, prov_role=ProvRole.AUTHOR_ISSUE
            ),
            annotations=[],
            # parse_annotations(raw_annotations),
            created_at=issue.created_at,
            closed_at=issue.closed_at,
        )

    def fetch_pullrequests(self):
        """
        all pull requests are issues, but not all issues are pull requests
        therefore, we can use the same api for some shared resources but not others

        pull requests can have comments (same as issues)
        https://docs.github.com/en/rest/reference/pulls#list-review-comments-on-a-pull-request
        users can add reactions to pull request comments (same as issues)
        https://docs.github.com/en/rest/reactions?apiVersion=2022-11-28#list-reactions-for-an-issue-comment
        to get the reactions for a pull request, we need to get the reactions for it as an issue
        https://docs.github.com/en/rest/reference/issues#list-reactions-for-an-issue
        pull requests can have labels (same as issues)
        https://docs.github.com/en/rest/reference/issues#list-labels-for-an-issue
        pull requests can have milestones (same as issues)
        https://docs.github.com/en/rest/reference/issues#list-milestones-for-an-issue
        pull requests can have events (same as issues)
        https://docs.github.com/en/rest/reference/issues#list-issue-events
        pull requests can have a timeline???? if treated as an issue (same as issues)
        https://docs.github.com/en/rest/reference/issues#list-timeline-events-for-an-issue
        pull requests can have reviews (grouped review comments with a state and optional body)
        https://docs.github.com/en/rest/reference/pulls#list-reviews-on-a-pull-request
        pull requests can have review comments
        https://docs.github.com/en/rest/reference/pulls#list-review-comments-on-a-pull-request
        pull requests review comment can have reactions
        https://docs.github.com/en/rest/reference/reactions#list-reactions-for-a-pull-request-review-comment
        """
        for pull in self.repository.get_pulls(state="all"):

            raw_annotations = []
            raw_annotations.extend(pull.get_comments())
            raw_annotations.extend(comment.get_reactions() for comment in pull.get_comments())
            raw_annotations.extend(pull.get_labels())
            raw_annotations.extend(pull.get_review_comments())
            raw_annotations.extend(
                comment.get_reactions() for comment in pull.get_review_comments()
            )
            raw_annotations.extend(pull.get_reviews())
            raw_annotations.extend(pull.as_issue().get_reactions())
            raw_annotations.extend(pull.as_issue().get_events())
            raw_annotations.extend(pull.as_issue().get_timeline())

            yield self.pull2ir(pull, raw_annotations=raw_annotations)

    @staticmethod
    def pull2ir(pull, raw_annotations):
        return GithubPullRequest(
            number=pull.number,
            id=pull.id,
            title=pull.title,
            body=pull.body,
            url=pull.url,
            head=pull.head.ref,
            base=pull.base.ref,
            author=User(
                name=pull.user.name,
                email=pull.user.email,
                prov_role=ProvRole.AUTHOR_PULL_REQUEST,
            ),
            annotations=[],
            # parse_annotations(raw_annotations),
            created_at=pull.created_at,
            closed_at=pull.closed_at,
            merged_at=pull.merged_at,
        )

    def fetch_releases(self):
        for release in self.repository.get_releases():
            yield self.release2ir(release)

    @staticmethod
    def release2ir(release):
        return Release(
            name=release.title,
            description=release.body,
            tag_name=release.tag_name,
            author=User(
                name=release.author.name,
                email=release.author.email,
                prov_role=ProvRole.AUTHOR_RELEASE,
            ),
            assets=[Asset(asset.url, asset.content_type) for asset in release.get_assets()],
            evidences=[],
            created_at=release.created_at,
            released_at=release.published_at,
        )

    def fetch_tags(self):
        for tag in self.repository.get_tags():
            yield self.tag2ir(tag)

    @staticmethod
    def tag2ir(tag):
        return Tag(
            name=tag.name,
            hexsha=tag.commit.sha,
            message=tag.commit.commit.message,
            author=User(
                name=tag.commit.author.name,
                email=tag.commit.author.email,
                prov_role=ProvRole.AUTHOR_TAG,
            ),
            created_at=tag.commit.commit.author.date,
        )
