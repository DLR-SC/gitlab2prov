import abc
import itertools
from urllib.parse import urlsplit
from pathlib import Path
from datetime import datetime

import git

from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvRole


EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def repository_filepath(url, fp):
    slug = urlsplit(url).path
    if not slug:
        return
    project = slug[1:].split("/")[1]
    return Path(fp) / project


def https_clone_url(url, token):
    _, gitlab, slug, *_ = urlsplit(url)
    return f"https://gitlab.com:{token}@{gitlab}{slug}"


class AbstractGitMiner(abc.ABC):
    def mine(self, repo: git.Repo):
        resources = self._mine(repo)
        return resources

    def get_repo(self, filepath: str):
        return self._get_repo(filepath)

    @abc.abstractmethod
    def _get_repo(self, filepath: str):
        raise NotImplementedError

    @abc.abstractmethod
    def _mine(self, repo: git.Repo):
        raise NotImplementedError


class GitRepositoryMiner(AbstractGitMiner):
    def _get_repo(self, filepath):
        try:
            return git.Repo(filepath)
        except (git.NoSuchPathError, git.InvalidGitRepositoryError) as err:
            return None

    def _mine(self, repo: git.Repo):
        return itertools.chain(extract_commits(repo), extract_files(repo))


def extract_commits(repo: git.Repo):
    for commit in repo.iter_commits("--all"):
        author, committer = commit.author, commit.committer
        author = objects.User(author.name, author.email, prov_role=ProvRole.Author)
        committer = objects.User(
            committer.name, committer.email, prov_role=ProvRole.Committer
        )
        parents = [parent.hexsha for parent in commit.parents]
        yield objects.GitCommit(
            commit.hexsha,
            commit.message,
            commit.summary,
            author,
            committer,
            parents,
            datetime.fromtimestamp(commit.authored_date),
            datetime.fromtimestamp(commit.committed_date),
        )


def parse_log_cmd(log: str):
    """Parse 'git log' output into file paths, commit hexshas, file status (or change types).

    Log example:
        34db8646fe1648bef9b7ce6613ae4a06acffba66
        A   foo.py
        9b65f80b44acffc8036fef932f801134533b99bd
        M   foo.py

    Parsed output:
        (foo.py, 34db8646fe1648bef9b7ce6613ae4a06acffba66, A)
        (foo.py, 9b65f80b44acffc8036fef932f801134533b99bd, M)
    """
    # split at line breaks, remove empty lines and superfluos whitespace
    lines = [line.strip() for line in log.split("\n") if line]
    # reorder such that file path, hexsha and status are on the same line
    hexshas = lines[::2]
    types = [line.split()[0][0] for line in lines[1::2]]
    paths = [line.split()[1][:] for line in lines[1::2]]
    return zip(paths, hexshas, types)


def extract_versions(repo: git.Repo, file: objects.File):
    versions = list()
    for path, hexsha, status in parse_log_cmd(
        repo.git.log(
            "--all", "--follow", "--name-status", "--pretty=format:%H", "--", file.path
        )
    ):
        versions.append(objects.FileRevision(path, hexsha, status, file))
    # versions are sorted young to old (last elem is oldest)
    for version, previous_version in itertools.zip_longest(versions, versions[1:]):
        version.previous = previous_version
    return list(versions)


def extract_files(repo: git.Repo):
    files = []
    for commit in repo.iter_commits("--all"):
        # choose the parent commit to diff against
        # use the *magic* empty tree sha for commits without parents
        parent = commit.parents[0] if commit.parents else EMPTY_TREE_SHA
        # diff against parent, set reverse to true TODO: why again?
        diff = commit.diff(parent, R=True)
        for entry in diff.iter_change_type("A"):
            # file path for new files is stored in b_path
            file = objects.File(entry.b_path, commit.hexsha)
            files.extend(extract_versions(repo, file))
    return files
