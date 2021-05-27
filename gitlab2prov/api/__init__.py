import asyncio

from aiohttp import ClientSession
from aiohttp.web import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPTooManyRequests,
    HTTPUnauthorized,
)
from collections import defaultdict, deque
from gitlab2prov.utils import group_by, url_encoded_path
from yarl import URL

from .ratelimiter import RateLimiter


def cache(func):
    cache = dict()

    async def memorized(self, *args, **kwargs):
        key = f"{func.__name__}:{id(self)}"
        if key not in cache:
            cache[key] = await func(self, *args, **kwargs)
        return cache[key]

    return memorized


class GitlabClient:
    def __init__(self, project_url, token, rate_limit):
        self.url_builder = URLBuilder(project_url)
        self.req_handler = RequestHandler(token, rate_limit)

    async def __aenter__(self):
        """
        Open request handler client session on.
        """
        self.req_handler = await self.req_handler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Close client request handler client session on.
        """
        await self.req_handler.__aexit__(exc_type, exc_val, exc_tb)

    def set_project_url(self, project_url):
        self.url_builder.set_project_url(project_url)

    async def request(self, path, path_values=None):
        urls = self.url_builder.build_urls(path, path_values)
        return await self.req_handler.request_all_pages(urls)

    @cache
    async def commits(self):
        path = "repository/commits"
        try:
            commits = (await self.request(path))[0]
        except HTTPNotFound as e404:
            # git repository might be disabled
            # continue without commits
            commits = []
        return commits

    @cache
    async def commit_diffs(self):
        if not await self.commits():
            return []
        path = "repository/commits/{}/diff"
        path_values = [(commit["id"],) for commit in await self.commits() if commit]
        diffs = await self.request(path, path_values)
        return diffs

    @cache
    async def commit_notes(self):
        if not await self.commits():
            return []
        path = "repository/commits/{}/discussions"
        path_values = [(commit["id"],) for commit in await self.commits()]
        discussions_grouped_by_commit = await self.request(path, path_values)
        notes_grouped_by_commit = []
        for discussions in discussions_grouped_by_commit:
            notes = [note for discussion in discussions for note in discussion["notes"]]
            notes_grouped_by_commit.append(notes)
        return notes_grouped_by_commit

    @cache
    async def issues(self):
        path = "issues"
        return (await self.request(path))[0]

    @cache
    async def issue_labels(self):
        if not await self.issues():
            return []
        path = "issues/{}/resource_label_events"
        path_values = [(issue["iid"],) for issue in await self.issues()]
        return await self.request(path, path_values)

    @cache
    async def issue_awards(self):
        if not await self.issues():
            return []
        path = "issues/{}/award_emoji"
        path_values = [(issue["iid"],) for issue in await self.issues()]
        return await self.request(path, path_values)

    @cache
    async def issue_notes(self):
        if not await self.issues():
            return []
        path = "issues/{}/notes"
        path_values = [(issue["iid"],) for issue in await self.issues()]
        return await self.request(path, path_values)

    @cache
    async def issue_note_awards(self):
        if not await self.issue_notes():
            return []
        path = "issues/{}/notes/{}/award_emoji"
        path_values = []
        for notes in await self.issue_notes():
            for note in notes:
                if note["system"]:
                    continue
                tpl = (note["noteable_iid"], note["id"])
                path_values.append(tpl)
        if not path_values:
            return [list() for _ in await self.issues()]
        awards_grouped_by_note = await self.request(path, path_values)
        notes_per_issue = [len(notes) for notes in await self.issue_notes()]
        return group_by(awards_grouped_by_note, notes_per_issue)

    @cache
    async def merge_requests(self):
        path = "merge_requests"
        try:
            merge_requests = (await self.request(path))[0]
        except HTTPForbidden as e403:
            # merge requests might be disabled
            # continue without merge requests
            merge_requests = []
        return merge_requests

    @cache
    async def merge_request_labels(self):
        if not await self.merge_requests():
            return []
        path = "merge_requests/{}/resource_label_events"
        path_values = [
            (merge_request["iid"],) for merge_request in await self.merge_requests()
        ]
        return await self.request(path, path_values)

    @cache
    async def merge_request_awards(self):
        if not await self.merge_requests():
            return []
        path = "merge_requests/{}/award_emoji"
        path_values = [
            (merge_request["iid"],) for merge_request in await self.merge_requests()
        ]
        return await self.request(path, path_values)

    @cache
    async def merge_request_notes(self):
        if not await self.merge_requests():
            return []
        path = "merge_requests/{}/notes"
        path_values = [
            (merge_request["iid"],) for merge_request in await self.merge_requests()
        ]
        return await self.request(path, path_values)

    @cache
    async def merge_request_note_awards(self):
        if not await self.merge_request_notes():
            return []
        path = "merge_requests/{}/notes/{}/award_emoji"
        path_values = []
        for notes in await self.merge_request_notes():
            for note in notes:
                if note["system"]:
                    continue
                vs = (note["noteable_iid"], note["id"])
                path_values.append(vs)
        if not path_values:
            return [list() for _ in await self.merge_request_notes()]
        awards_grouped_by_note = await self.request(path, path_values)
        notes_per_merge_request = [
            len(notes) for notes in await self.merge_request_notes()
        ]
        awards_grouped_by_merge_request = group_by(
            awards_grouped_by_note, notes_per_merge_request
        )
        return awards_grouped_by_merge_request

    @cache
    async def releases(self):
        path = "releases"
        try:
            releases = (await self.request(path))[0]
        except HTTPForbidden as e403:
            releases = []
        return releases

    @cache
    async def tags(self):
        path = "repository/tags"
        try:
            tags = (await self.request(path))[0]
        except HTTPForbidden as e403:
            tags = []
        return tags


class URLBuilder:
    def __init__(self, project_url):
        self.api_path = "api/v4/projects"
        project_url = URL(project_url)
        self.base_url = project_url.origin()
        self.project_id = url_encoded_path(project_url.path)

    def set_project_url(self, url):
        self.__init__(url)

    def build_paths(self, path, path_values=None):
        if path.startswith("/"):
            path = path[1:]
        path = f"{self.api_path}/{self.project_id}/{path}"
        if not path_values:
            return [path]
        paths = []
        for values in path_values:
            if path.count("{}") != len(values):
                raise ValueError("")
            paths.append(path.format(*values))
        return paths

    def build_urls(self, path, path_values=None):
        """
        Build a list of urls from a path and a list of placeholder values.

        The path string can contain placeholders just like a string used in
        the f-string or .format string syntax.
        """
        urls = []
        paths = self.build_paths(path, path_values)
        query = "per_page=100"
        for path in paths:
            url = self.base_url.with_path(path, encoded=True).with_query(query)
            urls.append(url)
        return urls


class RequestHandler:
    def __init__(self, token, rate_limit, batch_size=200):
        self.token = token
        self.rate_limit = rate_limit
        self.batch_size = batch_size
        self.requests = defaultdict(deque)
        self.client = None

    async def __aenter__(self):
        auth = {"Private-Token": self.token}
        client = ClientSession(headers=auth)
        self.client = RateLimiter(client, rate=self.rate_limit)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()
        return

    @staticmethod
    def validate_response(url, response):
        if response.status == 401:
            # TODO
            # token invalid
            # how to handle: user should be notified (raise)
            raise HTTPUnauthorized
        elif response.status == 403:
            # TODO
            # returned for merge request endpoint if endpoint disabled in project settings
            # how to handle: return an empty list for clt.merge_requests() (catch)
            # else: raise and stop execution
            raise HTTPForbidden
        elif response.status == 404:
            # TODO
            # a) returned when url leads to nothing (raise)
            # b) returned for commits when repository endpoint disabled in project settings
            # b) how to handle: return an empty list for clt.commits() (catch & log)
            raise HTTPNotFound
        elif response.status == 429:
            # TODO
            # to many requests in too little time (raise/catch?)
            # reason: rate limit set too high
            # how to handle 1: wait for specified time, then continue requesting (catch & log)
            # how to handle 2: inform user about rate limits (gitlab.com defaults to 100)
            # how to handle 3: link to github api with rate limit info
            raise HTTPTooManyRequests
        return True

    async def request_page(self, url, page=1):
        url = url.update_query({"page": page})
        async with await self.client.get(url) as resp:
            self.validate_response(url, resp)
            json = await resp.json()
        self.queue_next_page_requests(url, resp, page)
        return json

    def queue_next_page_requests(self, url, response, current_page):
        key = url.with_query("")
        if "x-total-pages" in response.headers and current_page == 1:
            total_pages = int(response.headers["x-total-pages"])
            for page in range(2, total_pages + 1):
                self.requests[key].append(self.request_page(url, page))
        elif "x-total-pages" not in response.headers:
            next_page = response.headers["x-next-page"]
            next_page = 0 if not next_page else int(next_page)
            if current_page < next_page:
                self.requests[key].append(self.request_page(url, next_page))

    def get_queued_requests(self, max_n):
        pairs = []
        for url, requests in self.requests.items():
            for _ in range(max_n):
                if not requests:
                    break
                pairs.append((url, requests.popleft()))
        return pairs

    def queued_requests_exist(self):
        return any(requests for requests in self.requests.values())

    async def request_all_pages(self, urls):
        for url in urls:
            key = url.with_query("")
            self.requests[key].append(self.request_page(url))
        responses = defaultdict(list)
        while self.queued_requests_exist():
            pairs = self.get_queued_requests(self.batch_size)
            urls = [url for url, _ in pairs]
            requests = [request for _, request in pairs]
            pages = await asyncio.gather(*requests)
            for url, page in zip(urls, pages):
                responses[url].append(page)
        return [
            [entry for page in pages for entry in page] for pages in responses.values()
        ]
