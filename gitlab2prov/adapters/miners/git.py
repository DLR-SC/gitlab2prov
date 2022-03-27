from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from itertools import zip_longest

from git import Repo

from gitlab2prov.domain.constants import ProvRole, ChangeType
from gitlab2prov.domain.objects import User, GitCommit, File, FileRevision


EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


@dataclass
class AbstractMiner(ABC):
    @abstractmethod
    def mine(self):
        raise NotImplementedError


@dataclass
class GitRepositoryMiner(AbstractMiner):
    repo: Repo

    def mine(self):
        yield from extract_commits(self.repo)
        yield from extract_files(self.repo)
        yield from extract_revisions(self.repo)


def get_author(commit):
    return User(
        name=commit.author.name,
        email=commit.author.email,
        gitlab_username=None,
        gitlab_id=None,
        prov_role=ProvRole.AUTHOR,
    )


def get_committer(commit):
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


def extract_commits(repo):
    for commit in repo.iter_commits("--all"):
        yield GitCommit(
            hexsha=commit.hexsha,
            message=commit.message,
            title=commit.summary,
            author=get_author(commit),
            committer=get_committer(commit),
            parents=[parent.hexsha for parent in commit.parents],
            prov_start=datetime.fromtimestamp(commit.authored_date),
            prov_end=datetime.fromtimestamp(commit.committed_date),
        )


def extract_files(repo):
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
            yield File(path=diff_item.b_path, committed_in=commit.hexsha)


def extract_revisions(repo):
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
            revs.append(
                FileRevision(
                    path=path, committed_in=hexsha, change_type=status, original=file
                )
            )
        # revisions remeber their predecessor (previous revision)
        for rev, prev in zip_longest(revs, revs[1:]):
            rev.previous = prev
            yield rev
