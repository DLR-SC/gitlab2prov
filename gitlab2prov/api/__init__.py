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

    async def request(self, path, path_values=None, query="", query_values=None):
        urls = self.url_builder.build_urls(path, path_values, query, query_values)
        return await self.req_handler.request_all_pages(urls)

    @cache
    async def commits(self):
        path = "repository/commits"
        commits = (await self.request(path))[0]
        return commits

    @cache
    async def commit_diffs(self):
        if not await self.commits():
            return []
        path = "repository/commits/{}/diff"
        path_values = [(commit["id"],) for commit in await self.commits() if commit]
        return await self.request(path, path_values)

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
        return (await self.request(path))[0]

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
        return (await self.request(path))[0]

    @cache
    async def tags(self):
        path = "repository/tags"
        return (await self.request(path))[0]


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

    @staticmethod
    def build_queries(query="", query_values=None):
        # remove leading '?'
        if query.startswith("?"):
            query = query[1:]
        # split query into single parts; (delimiter '&')
        parts = [part for part in query.split("&") if part]
        # add 'per_page' parameter to query parts
        parts.append("per_page=100")
        query = f"{'&'.join(parts)}"
        if not query_values:
            return [query]
        queries = []
        for values in query_values:
            if query.count("{}") != len(values):
                raise ValueError("")
            queries.append(query.format(*values))
        return queries

    def build_urls(self, path, path_values=None, query="", query_values=None):
        paths = self.build_paths(path, path_values)
        queries = self.build_queries(query, query_values)
        pairs = []
        if len(paths) == len(queries):
            pairs = zip(paths, queries)
        elif len(paths) == 1:
            path = paths[0]
            pairs = [(path, query) for query in queries]
        elif len(queries) == 1:
            query = queries[0]
            pairs = [(path, query) for path in paths]
        urls = []
        for path, query in pairs:
            url = self.base_url.with_path(path, encoded=True).with_query(query)
            urls.append(url)
        return urls

            fmt = path.format(*values[:path.count("{}")])
            if query:
                fmt_query = {
                    val.split("=")[0]: val.split("=")[1]
                    for val in query.format(*values[path.count("{}"):]).split("&")}
            else:
                fmt_query = {}

            url = self.base.origin().with_path(self.base.raw_path + fmt, encoded=True)
            ret = url.update_query({**fmt_query, "per_page": 50})
            yield ret


@dataclass
class RequestHandler:
    """
    Dispatch requests asynchronously, though adhere to rate limiting.
    """
    token: str
    rate: int = 10
    session: Optional[RateLimiter] = None

    async def __aenter__(self) -> RequestHandler:
        """
        Create client session with authorization info.
        """
        auth = {"Private-Token": self.token}
        self.session = RateLimiter(ClientSession(headers=auth), rate=self.rate)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Close client session.
        """
        if not self.session:
            return
        await self.session.close()

    async def first_page(self, url: URL) -> Tuple[Any, int]:
        """
        Return content of first page and number of total pages.
        """
        if not self.session:
            raise ValueError

        url = url.update_query({"page": 1})

        async with await self.session.get(url) as resp:
            status = resp.status
            if status == 403:
                return [], 1
            if status != 200:
                msg = "A GET request got an unexpected status code response!"
                http_status = f"HTTP Status Code: {status}"
                concerned_url = f"Concerned URL: {url}"
                raise Exception(msg + "\n" + http_status + "\n" + concerned_url)
            json = await resp.json()
            page_count = int(resp.headers.get("x-total-pages", 1))

        return json, page_count

    async def single_page(self, url: URL, page: int) -> Any:
        """
        Return json content of page number *page* of request *url*.
        """
        if not self.session:
            raise ValueError

        url = url.update_query({"page": page})

        async with await self.session.get(url) as resp:
            status = resp.status
            if status != 200:
                msg = "A GET request got an unexpected status code response!"
                http_status = f"HTTP Status Code: {status}"
                concerned_url = f"Concerned URL: {url}"
                raise Exception(msg + "\n" + http_status + "\n" + concerned_url)
            json = await resp.json()

        return json

    async def request(self, urls: Iterable[URL]) -> List[Any]:
        """
        Return content of all pages for each url in *urls*

        Workflow of this method:

        1. Asynchronously request first page and page count for all
            urls.

        2. Create request tasks for the remaining pages of urls that
            have more than one content page.

        3. Dispatch tasks batches asynchronously.

        4. Match remaining pages with their corresponding first.

        5. Return as one big page for all urls.
        """
        urls = list(urls)

        # create tasks for first pages
        tasks = [self.first_page(url) for url in urls]
        # collect first pages
        first_pages = await self.gather_in_batches(tasks)

        # create tasks for remaining pages
        tasks = []
        for url, (_, page_count) in zip(urls, first_pages):
            if page_count < 2:
                continue
            remaining = [self.single_page(url, n) for n in range(2, page_count + 1)]
            tasks.extend(remaining)

        # collect remaining pages
        remaining_pages = deque(await self.gather_in_batches(tasks))

        if not remaining_pages:
            return [page for (page, _) in first_pages]

        # extend first page of each request to
        # hold the entire content of all pages
        results: List[Any] = []
        for (page, page_count) in first_pages:
            for _ in range(2, page_count + 1):
                page.extend(remaining_pages.popleft())
            results.append(page)

        return results

    @staticmethod
    async def gather_in_batches(coroutines: List[Coroutine[Any, Any, T]]) -> List[T]:
        """
        Perform a limited amount of requests per asyncio.gather statement.

        Prevent segfault when matching queries to their answers.
        """
        result: List[T] = []

        for coroutine_batch in chunks(coroutines, 200):
            result.extend(await asyncio.gather(*coroutine_batch))

        return result
