from copy import deepcopy
from urllib.parse import urlparse, urlunparse
import asyncio
from gitlab import Gitlab

from gl2p.translators import CommitTranslator
from gl2p.commons import FileAction
from gl2p.ratelimiter import RateLimiter
from gl2p.config import CONFIG


class Pipeline:
    def __init__(self):
        self.gitlab_api = None
        self.path = None
        self.project = None
        self.translator = None

        self._init_gitlab_api()
        self._init_project()

    def _init_gitlab_api(self):
        self.gitlab_api = Gitlab(
                url=CONFIG["GITLAB"]["url"],
                private_token=CONFIG["GITLAB"]["token"])

    def _init_project(self):
        self.path = self._pathify(CONFIG["GITLAB"]["project"])
        self.project = self.gitlab_api.projects.get(self.path)
        self.path = self.path.replace("/", "%2F")  # url encoded path

    def _pathify(self, url):
        # NOTE: remove leading slash
        return urlparse(url).path.replace("/", "", 1)

    def request_data(self, *args, **kwargs):
        raise NotImplementedError()

    def process_data(self, *args, **kwargs):
        raise NotImplementedError()

    def translate_data(self, *args, **kwargs):
        raise NotImplementedError()

    def commit_data(self, *args, **kwargs):
        raise NotImplementedError()


class CommitPipeline(Pipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = CommitTranslator()
        self.commits = None
        self.diffs = None

    def request_data(self):
        import time
        self.commits = self.project.commits.list(all=True)
        print(f"Estimated time to fetch diffs: {len(self.commits)/10} seconds")
        t = time.time()
        self.diffs = self._get_diffs()
        print(f"Got {len(self.diffs)} diffs in {time.time() - t}")

    def process_data(self):
        updated = []
        for commit, diff in zip(self.commits, self.diffs):
            for entry in diff:
                copy = deepcopy(commit)
                copy.used = entry["old_path"]
                copy.generated = entry["new_path"]
                copy.file_action = self._get_file_action(entry)
                updated.append(copy)
        self.commits = updated

    def translate_data(self, *args, **kwargs):
        self.translator.translate(self.commits)

    def commit_data(self, *args, **kwargs):
        self.translator.clean()
        return self.translator.prov

    def _get_file_action(self, entry):
        if entry["new_file"]:
            return FileAction.ADDED
        elif entry["deleted_file"]:
            return FileAction.DELETED
        return FileAction.MODIFIED

    def _get_diffs(self):
        urls = self._get_urls()
        return asyncio.run(self._fetch(urls))

    def _get_urls(self):
        parsed = urlparse(CONFIG["GITLAB"]["url"])._asdict()
        urls = []
        for commit in self.commits:
            path = "/api/v4/projects/{}/repository/commits/{}/diff"
            parsed["path"] = path.format(self.path, commit.id)
            urls.append(urlunparse(tuple(parsed.values())))
        return urls

    async def _fetch(self, urls):
        # NOTE: Send authentification header with each request
        auth = {"Private-Token": CONFIG["GITLAB"]["token"]}
        async with RateLimiter(headers=auth) as client:
            tasks = [
                    asyncio.ensure_future(self._fetch_one(client, url))
                    for url in urls
                    ]
            return await asyncio.gather(*tasks)

    async def _fetch_one(self, client, url):
        async with await client.get(url) as resp:
            resp = await resp.json()
            return resp


class IssuePipeline(Pipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = None  # IssueTranslator
        self.issues = None

    def request_data(self):
        pass

    def process_data(self):
        pass

    def translate_data(self):
        pass

    def commit_data(self):
        pass
