from collections.abc import Iterator
from dataclasses import dataclass
from tempfile import TemporaryDirectory

from git import Commit
from git import Repo

from gitlab2prov.adapters.fetch.utils import clone_over_https_url
from gitlab2prov.domain.constants import ChangeType
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import File
from gitlab2prov.domain.objects import FileRevision
from gitlab2prov.domain.objects import GitCommit
from gitlab2prov.domain.objects import User


LOG_DELIMITER = "====DELIMITER===="
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


@dataclass
class GitFetcher:
    url: str
    token: str

    _repo: Repo | None = None
    _tmpdir: TemporaryDirectory | None = None

    def __enter__(self):
        self._tmpdir = TemporaryDirectory(ignore_cleanup_errors=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._repo:
            self._repo.close()
        if self._tmpdir:
            self._tmpdir.cleanup()

    def do_clone(self) -> None:
        url = clone_over_https_url(self.url, self.token)
        self._repo = Repo.clone_from(
            url=url,
            to_path=self._tmpdir.name,
        )

    def fetch_git(self) -> Iterator[GitCommit | File | FileRevision]:
        for commit in self._repo.iter_commits("--all"):
            yield self.git_commit_to_domain_commit(commit)
            for file in self.fetch_files_for_commit(commit):
                yield file
                for revision in self.fetch_revisions_for_file(file):
                    yield revision
                    
    @staticmethod
    def git_commit_to_domain_commit(commit: Commit) -> GitCommit:
        return GitCommit(
            hexsha=commit.hexsha,
            message=commit.message,
            title=commit.summary,
            author=get_author(commit),
            committer=get_committer(commit),
            parents=[parent.hexsha for parent in commit.parents],
            prov_start=commit.authored_datetime,
            prov_end=commit.committed_datetime,
        )
        
    def fetch_files_for_commit(self, commit: Commit) -> Iterator[File]:
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
    
    def fetch_revisions_for_file(self, file: File) -> Iterator[FileRevision]:
        log = self._repo.git.log(
            "--all",
            "--follow",
            "--name-status",
            f"--pretty=format:{LOG_DELIMITER}%n%H",
            "--",
            file.path,
        )

        prev_revision = None

        for hexsha, status, path in reversed(list(parse_log(log))):
            revision = FileRevision(
                path=path,
                committed_in=hexsha,
                change_type=status,
                original=file,
                previous=prev_revision,
            )
            yield revision
            prev_revision = revision


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
    """Parse 'git log' output into file paths, commit hexshas, file status (aka change type)."""
    # split the log into single entries using the delimiter
    for entry in log.split(f"{LOG_DELIMITER}\n"):
        # skip empty entries
        if not entry:
            continue
        # split the entry into lines, remove empty lines
        lines = [line.strip() for line in entry.split("\n") if line]
        # first line is always the commit hexsha
        hexsha = lines[0]
        for line in lines[1:]:
            # split the line by tab characters
            parts = line.split("\t")
            # status is the first character in the line
            status = parts[0][0]
            # path is always the last element when split by tab
            path = parts[-1]
            yield hexsha, status, path
        