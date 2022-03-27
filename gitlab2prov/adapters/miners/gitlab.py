import abc
from typing import TypeAlias
import itertools

import gitlab.v4.objects

from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.adapters.miners.annotation_parsing import parse_annotations


Project: TypeAlias = gitlab.v4.objects.Project



class AbstractGitlabMiner(abc.ABC):
    def mine(self, project: Project):
        resources = self._mine(project)
        return resources

    def get_project(self, url, token):
        return self._get_project(url, token)

    @abc.abstractmethod
    def _get_project(self, url: str, token: str):
        raise NotImplementedError

    @abc.abstractmethod
    def _mine(self, project: Project):
        raise NotImplementedError


class GitlabProjectMiner(AbstractGitlabMiner):

    def _mine(self, project: Project):
        return itertools.chain(
            extract_gitlab_commits(project),
            extract_issues(project),
            extract_mergerequests(project),
            extract_releases(project),
            extract_tags(project),
        )


def extract_gitlab_commits(project: Project):
    for commit in project.commits.list(all=True):
        parseables = set()
        parseables.update(commit.comments.list(all=True))
        parseables.update(commit.comments.list(all=True, system=True))
        annotations = parse_annotations(parseables)
        author = objects.User(
            commit.committer_name,
            commit.committer_email,
            prov_role=ProvRole.GitlabCommitAuthor,
        )
        yield objects.GitlabCommit(
            commit.id,
            commit.web_url,
            author,
            annotations,
            commit.authored_date,
            commit.committed_date,
        )


def extract_issues(project: Project):
    for issue in project.issues.list(all=True):
        parseables = set()
        parseables.update(issue.notes.list(all=True))
        parseables.update(issue.notes.list(all=True, system=True))
        parseables.update(issue.resourcelabelevents.list(all=True))
        parseables.update(issue.awardemojis.list(all=True))
        parseables.update(
            award
            for note in issue.notes.list(all=True)
            for award in note.awardemojis.list(all=True)
        )
        annotations = parse_annotations(parseables)
        author = objects.User(
            issue.author.get("name"),
            issue.author.get("email"),
            issue.author.get("username"),
            issue.author.get("id"),
            ProvRole.IssueAuthor,
        )
        yield objects.Issue(
            issue.id,
            issue.iid,
            issue.title,
            issue.description,
            issue.web_url,
            author,
            annotations,
            issue.created_at,
            issue.closed_at,
        )


def extract_mergerequests(project: Project):
    for mergerequest in project.mergerequests.list(all=True):
        parseables = set()
        parseables.update(mergerequest.notes.list(all=True))
        parseables.update(mergerequest.notes.list(all=True, system=True))
        parseables.update(mergerequest.awardemojis.list(all=True))
        parseables.update(mergerequest.resourcelabelevents.list(all=True))
        parseables.update(
            award
            for note in mergerequest.notes.list(all=True)
            for award in note.awardemojis.list(all=True)
        )
        annotations = parse_annotations(parseables)
        author = objects.User(
            mergerequest.author.get("name"),
            mergerequest.author.get("email"),
            mergerequest.author.get("username"),
            mergerequest.author.get("id"),
            ProvRole.MergeRequestAuthor,
        )
        yield objects.MergeRequest(
            mergerequest.id,
            mergerequest.iid,
            mergerequest.title,
            mergerequest.description,
            mergerequest.web_url,
            mergerequest.source_branch,
            mergerequest.target_branch,
            author,
            annotations,
            mergerequest.created_at,
            mergerequest.closed_at,
            mergerequest.merged_at,
            getattr(mergerequest, "first_deployed_to_production_at", None),
        )


def extract_releases(project: Project):
    for release in project.releases.list(all=True):
        author = None
        if hasattr(release, "author"):
            author = objects.User(
                release.author.get("name"),
                release.author.get("email"),
                release.author.get("username"),
                release.author.get("id"),
                ProvRole.ReleaseAuthor,
            )
        assets = [
            objects.Asset(asset.get("url"), asset.get("format"))
            for asset in release.assets.get("sources")
        ]
        evidences = [
            objects.Evidence(
                evidence.get("sha"),
                evidence.get("filepath"),
                evidence.get("collected_at"),
            )
            for evidence in release.evidences
        ]
        yield objects.Release(
            release.name,
            release.description,
            release.tag_name,
            author,
            assets,
            evidences,
            release.created_at,
            release.released_at,
        )


def extract_tags(project: Project):
    for tag in project.tags.list(all=True):
        author = objects.User(
            tag.commit.get("author_name"),
            tag.commit.get("author_email"),
            prov_role=ProvRole.TagAuthor,
        )
        yield objects.Tag(
            tag.name, tag.target, tag.message, author, tag.commit.get("created_at")
        )
