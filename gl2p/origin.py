# Data Sources for REST api connections 

# standard lib imports
from collections import namedtuple
from urllib.parse import urlparse, urlunparse
# third party imports
from gitlab import Gitlab
# local imports
from gl2p.config import CONFIG
from gl2p.commons import Commit, File, Actor, Time, FileStatus, Container
from gl2p.helpers import pathify
from gl2p.network import RateLimitedAsyncRequestHandler


class Origin:

    def __init__(self):
        self.client = None
        self.data = None

    def _register_client(self):
        raise NotImplementedError()

    def fetch(self):
        # data retrieval
        raise NotImplementedError()

    def process(self):
        # data processing
        raise NotImplementedError()


class GitLabOrigin(Origin):

    def __init__(self):
        super().__init__()
        self._register_client()

    def _register_client(self):
        url = CONFIG["GITLAB"]["url"]
        token = CONFIG["GITLAB"]["token"]
        self.client = Gitlab(url, private_token=token)

    def fetch(self):
        purl = CONFIG["GITLAB"]["project"]
        project = self.client.projects.get(pathify(purl))

        # -- commits --
        commits = project.commits.list(all=True)

        # -- diffs --
        # build urls that have to be requested.
        urls = []
        parsed = urlparse(CONFIG["GITLAB"]["url"])._asdict()
        for commit in commits:
            path = "/api/v4/projects/{}/repository/commits/{}/diff"
            parsed["path"] = path.format(pathify(purl), commit.id)
            urls.append(urlunparse(tuple(parsed.values())))
        # pass urls to request handling
        async_client = RateLimitedAsyncRequestHandler()
        diffs = async_client.get_batch(urls)

        # store retrieved data
        data = namedtuple("data", "commits diffs")
        self.data = data(commits, diffs)

    def process(self):
        commits = []
        for commit, diff in zip(self.data.commits, self.data.diffs):

            # -- files --
            files = []
            for entry in diff:
                status = None
                if entry["new_file"]: 
                    status = FileStatus.ADDED
                elif entry["deleted_file"]:
                    status = FileStatus.DELETED
                else:
                    status = FileStatus.MODIFIED
                f = File(commit_sha=commit.id,
                        old_path=entry["old_path"],
                        new_path=entry["new_path"],
                        status=status)
                files.append(f)

            # -- commits --
            author = Actor(commit.author_name, commit.author_email)
            committer = Actor(commit.committer_name, commit.committer_email)
            time = Time(commit.authored_date, commit.committed_date)
            parents = [cid for cid in commit.parent_ids]
            commits.append(Commit(commit.id, commit.message, time, author, committer, parents, files))

        # store accumulated data in Container
        return Container(commits)
