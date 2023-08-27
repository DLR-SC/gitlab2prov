from collections.abc import Iterator
from dataclasses import dataclass
from itertools import zip_longest
from tempfile import TemporaryDirectory
from pathlib import Path

from git import Commit
from git import Repo

from gitlab2prov.adapters.project_url import ProjectUrl
from gitlab2prov.domain.constants import ChangeType
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import File
from gitlab2prov.domain.objects import FileRevision
from gitlab2prov.domain.objects import GitCommit
from gitlab2prov.domain.objects import User


EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


@dataclass
class GitFetcher:
    project_url: type[ProjectUrl]
    repo: Repo | None = None
    tmpdir: TemporaryDirectory | None = None

    def __enter__(self):
        self.tmpdir = TemporaryDirectory(ignore_cleanup_errors=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.repo:
            self.repo.close()
        if self.tmpdir:
            self.tmpdir.cleanup()

    def do_clone(self, url: str, token: str) -> None:
        clone_url = self.project_url(url).clone_url(token)
        self.repo = Repo.clone_from(clone_url, self.tmpdir.name)

    def fetch_all(self) -> Iterator[GitCommit | File | FileRevision]:
        yield from extract_commits(self.repo)
        yield from extract_files(self.repo)
        yield from extract_revisions(self.repo)


def get_author(commit: Commit) -> User:
    return User(
        name=commit.author.name,
        email=commit.author.email,
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.AUTHOR,
    )


def get_committer(commit: Commit) -> User:
    return User(
        name=commit.committer.name,
        email=commit.committer.email,
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.COMMITTER,
    )


def parse_log(log: str):
    """Parse 'git log' output into file paths, commit hexshas, file status (aka change type).
    Example:
    >>> parse_log(
            '''
            34db8646fe1648bef9b7ce6613ae4a06acffba66
            A   foo.py
            9b65f80b44acffc8036fef932f801134533b99bd
            M   foo.py
            '''
        )
    [(foo.py, 34db8646fe1648bef9b7ce6613ae4a06acffba66, A), (foo.py, 9b65f80b44acffc8036fef932f801134533b99bd, M)]
    """
    # split at line breaks, strip whitespace, remove empty lines
    lines = [line.strip() for line in log.split("\n") if line]
    # every second line contains the SHA1 of a commit
    hexshas = lines[::2]
    # every other line contains a type, aswell as a file path
    types = [line.split()[0][0] for line in lines[1::2]]
    paths = [line.split()[1][:] for line in lines[1::2]]
    # zip all three together
    return zip(paths, hexshas, types)


def extract_commits(repo: Repo) -> Iterator[GitCommit]:
    for commit in repo.iter_commits("--all"):
        yield GitCommit(
            sha=commit.hexsha,
            title=commit.summary,
            message=commit.message,
            author=get_author(commit),
            committer=get_committer(commit),
            deletions=commit.stats.total["deletions"],
            insertions=commit.stats.total["insertions"],
            lines=commit.stats.total["lines"],
            files_changed=commit.stats.total["files"],
            parents=[parent.hexsha for parent in commit.parents],
            authored_at=commit.authored_datetime,
            committed_at=commit.committed_datetime,
        )


def extract_files(repo: Repo) -> Iterator[File]:
    for commit in repo.iter_commits("--all"):
        # choose the parent commit to diff against
        # use *magic* empty tree sha for commits without parents
        parent = commit.parents[0] if commit.parents else EMPTY_TREE_SHA
        # diff against parent
        diff = commit.diff(parent, R=True)
        # only consider files that have been added to the repository
        # disregard modifications and deletions
        for diff_item in diff.iter_change_type(ChangeType.ADDED):
            # path for new files is stored in diff b_path
            yield File(
                name=Path(diff_item.b_path).name, path=diff_item.b_path, commit=commit.hexsha
            )


def extract_revisions(repo: Repo) -> Iterator[FileRevision]:
    for file in extract_files(repo):
        revs = []

        for path, hexsha, status in parse_log(
            repo.git.log(
                "--all",
                "--follow",
                "--name-status",
                "--pretty=format:%H",
                "--",
                file.path,
            )
        ):
            status = {"A": "added", "M": "modified", "D": "deleted"}.get(status, "modified")
            revs.append(
                FileRevision(
                    name=Path(path).name,
                    path=path,
                    commit=hexsha,
                    status=status,
                    insertions=0,
                    deletions=0,
                    lines=0,
                    score=0,
                    file=file,
                )
            )
        # revisions remember their predecessor (previous revision)
        for rev, prev in zip_longest(revs, revs[1:]):
            rev.previous = prev
            yield rev
