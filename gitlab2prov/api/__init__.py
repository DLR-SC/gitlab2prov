from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import InitVar, dataclass
from typing import (Any, Callable, Coroutine, Dict, Iterable, Iterator, List,
                    Optional, Sequence, Tuple, TypeVar, cast)

from aiohttp import ClientSession
from yarl import URL

from gitlab2prov.utils import chunks, url_encoded_path
from gitlab2prov.utils.types import Award, Commit, Diff, Issue, Label, MergeRequest, Note
from gitlab2prov.api.ratelimiter import RateLimiter

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def alru_cache(func: F) -> F:
    """
    Typed lru cache decorator wrapping async coroutines.
    Creates a cache entry for each wrapped instance.

    Preserve the type signature of the wrapped function.
    Cache the return value of a function F on it's first execution.
    Return that value for every call of F after the first.
    """
    cache: Dict[str, Any] = dict()

    async def memorized(self: GitlabAPIClient) -> Any:
        # use method name and instance id as cache key
        key = func.__name__ + str(id(self))
        if key not in cache:
            # exec call on miss
            # store result in cache
            cache[key] = await func(self)
        return cache[key]

    return cast(F, memorized)


@dataclass
class GitlabAPIClient:
    """A wrapper for the GitLab project API."""
    purl: InitVar[str]
    token: InitVar[str]
    rate: InitVar[int]

    def __post_init__(self, purl: str, token: str, rate: int) -> None:
        self.url_builder = URLBuilder(purl)
        self.request_handler = RequestHandler(token, rate)

    async def __aenter__(self) -> GitlabAPIClient:
        """
        Open client session of request handler.
        """
        self.request_handler = await self.request_handler.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Close client session of request handler.
        """
        await self.request_handler.__aexit__(exc_type, exc_val, exc_tb)

    @alru_cache
    async def commits(self) -> List[Commit]:
        """
        Return list of commits of the wrapped project repository.
        """
        path = "repository/commits"
        url = self.url_builder.build(path)

        commits: List[Commit] = []

        for sublist in await self.request_handler.request(url):
            for commit in sublist:
                commits.append(commit)

        return commits

    @alru_cache
    async def commit_diffs(self) -> List[Diff]:
        """
        Return list of commit diffs of the wrapped project repository.

        Same order of commits as in self.commits. (zipable)
        """
        commits = await self.commits()

        if not commits:
            return []

        path_default = "repository/commits/{}/diff"
        path_compare = "repository/compare?from={}&to={}"

        urls = []
        for commit in commits:
            id_ = commit["id"]
            parent_ids = commit["parent_ids"]
            urls.append(list(self.url_builder.build(path_default, [(id_,)]))[0])
            continue

            if not parent_ids:
                urls.append(list(self.url_builder.build(path_default, [(id_,)]))[0])
            else:
                urls.append(list(self.url_builder.build(path_compare, [(parent_ids[0], id_)]))[0])

        diffs = []
        for diff in await self.request_handler.request(urls):
            cut_diff = []
            for entry in diff["diffs"] if isinstance(diff, dict) else diff:
                del entry["diff"]
                cut_diff.append(entry)
            diffs.append(cut_diff)
        return diffs

    @alru_cache
    async def commit_notes(self) -> List[List[Note]]:
        """
        Return list of commit notes for each commit of the wrapped
        project repository.
        """
        commits = await self.commits()

        if not commits:
            return []

        path = "repository/commits/{}/discussions"
        inserts = [(c["id"],) for c in commits]
        urls = self.url_builder.build(path, inserts)

        commit_notes: List[List[Note]] = []

        for commit in await self.request_handler.request(urls):
            notes = [n for discussion in commit for n in discussion["notes"]]
            commit_notes.append(notes)
        return commit_notes

    @alru_cache
    async def issues(self) -> List[Issue]:
        """
        Return list of all issues of the wrapped project.
        """
        path = "issues"
        url = self.url_builder.build(path)

        issues: List[Issue] = []
        for sublist in await self.request_handler.request(url):
            for issue in sublist:
                issues.append(issue)
        return issues

    @alru_cache
    async def issue_labels(self) -> List[List[Label]]:
        """
        Return list of issue labels for each issue of the wrapped
        project.
        """
        issues = await self.issues()

        if not issues:
            return []

        path = "issues/{}/resource_label_events"
        inserts = [(i["iid"],) for i in issues]
        urls = self.url_builder.build(path, inserts)

        return await self.request_handler.request(urls)

    @alru_cache
    async def issue_awards(self) -> List[List[Award]]:
        """
        Return list of award emoji for each issue of the wrapped
        project.
        """
        issues = await self.issues()

        if not issues:
            return []

        path = "issues/{}/award_emoji"
        inserts = [(i["iid"],) for i in issues]
        urls = self.url_builder.build(path, inserts)

        return await self.request_handler.request(urls)

    @alru_cache
    async def issue_notes(self) -> List[List[Note]]:
        """
        Return list of issue notes for each issue of the wrapped
        project.
        """
        issues = await self.issues()

        if not issues:
            return []

        path = "issues/{}/notes"
        inserts = [(i["iid"],) for i in issues]
        urls = self.url_builder.build(path, inserts)

        return await self.request_handler.request(urls)

    @alru_cache
    async def issue_note_awards(self) -> List[List[Award]]:
        """
        Return list of award emoji that have been awarded
        to notes of an issue for each issue.
        """
        issue_notes = await self.issue_notes()

        if not issue_notes:
            return []

        path = "issues/{}/notes/{}/award_emoji"

        inserts = [
            (note["noteable_iid"], note["id"])
            for issue in issue_notes
            for note in issue
            if not note["system"]
        ]

        if not inserts:
            # do not perform requests
            # if no awardable notes exist
            return [list() for issue in issue_notes]

        urls = self.url_builder.build(path, inserts)
        result = await self.request_handler.request(urls)
        notes = []

        for note_count in (len(issue) for issue in issue_notes):

            notes.append([n for sublist in result[:note_count] for n in sublist])

            result = result[note_count:]

        return notes

    @alru_cache
    async def merge_requests(self) -> List[MergeRequest]:
        """
        Return list of all merge request of the wrapped project.
        """
        path = "merge_requests"
        url = self.url_builder.build(path)

        merge_requests: List[MergeRequest] = []

        for sublist in await self.request_handler.request(url):
            for merge_request in sublist:
                merge_requests.append(merge_request)

        return merge_requests

    @alru_cache
    async def merge_request_labels(self) -> List[List[Label]]:
        """
        Return list of all label events for each merge request of the
        wrapped project.
        """
        mrs = await self.merge_requests()

        if not mrs:
            return []

        path = "merge_requests/{}/resource_label_events"
        inserts = [(mr["iid"],) for mr in mrs]
        urls = self.url_builder.build(path, inserts)

        return await self.request_handler.request(urls)

    @alru_cache
    async def merge_request_awards(self) -> List[List[Award]]:
        """
        Return list of all award emoji for each merge request of the
        wrapped project.
        """
        mrs = await self.merge_requests()

        if not mrs:
            return []

        path = "merge_requests/{}/award_emoji"
        inserts = [(mr["iid"],) for mr in mrs]
        urls = self.url_builder.build(path, inserts)

        return await self.request_handler.request(urls)

    @alru_cache
    async def merge_request_notes(self) -> List[List[Note]]:
        """
        Return list of merge request notes for each merge request of
        the wrapped project.
        """
        mrs = await self.merge_requests()

        if not mrs:
            return []

        path = "merge_requests/{}/notes"
        inserts = [(mr["iid"],) for mr in mrs]
        urls = self.url_builder.build(path, inserts)

        return await self.request_handler.request(urls)

    @alru_cache
    async def merge_request_note_awards(self) -> List[List[Award]]:
        """
        Return list of award emoji that have been awarded to notes
        of a merge request for each merge request.
        """
        mrs_notes = await self.merge_request_notes()

        if not mrs_notes:
            return []

        path = "merge_requests/{}/notes/{}/award_emoji"
        inserts = [
            (note["noteable_iid"], note["id"])
            for mr in mrs_notes
            for note in mr
            if not note["system"]
        ]

        if not inserts:
            # do not perform requests
            # if no awardable notes exist
            return [list() for mr in mrs_notes]

        urls = self.url_builder.build(path, inserts)
        result = await self.request_handler.request(urls)
        notes = []

        # rematch note awards to the merge requests
        # that they have been awarded on

        for note_count in (len(mr) for mr in mrs_notes):

            notes.append([n for sublist in result[:note_count] for n in sublist])

            result = result[note_count:]

        return notes


@dataclass
class URLBuilder:
    """
    URL formatting and path building.
    """
    project_url: InitVar[str]
    base: URL = URL()

    def __post_init__(self, project_url: str) -> None:
        if not project_url:
            raise ValueError

        url = URL(project_url)

        if not url.scheme:
            raise ValueError

        p_id = url_encoded_path(url.path)
        self.base = url.origin().with_path(f"api/v4/projects/{p_id}", encoded=True)

    def build(self, path: str, inserts: Optional[Sequence[Tuple[str, ...]]] = None) -> Iterator[URL]:
        """
        Yield urls by appending *path* optionally formatted with values
        of *inserts* to self.base.

        Update query string to request 50 entries per page.
        """
        if inserts is None:
            inserts = []

        if path and not path.startswith("/"):
            path = "/" + path
        query = None
        if len(path.split("?")) == 2:
            path, query = path.split("?")

        if not inserts:
            if path.count("{}"):
                # blanks in path but insert list empty
                raise ValueError("Blanks exist. No values to insert.")
            url = self.base.origin().with_path(self.base.raw_path + path, encoded=True)
            ret = url.update_query({"per_page": 50})
            yield ret

        for values in inserts:
            if len(values) != (path.count("{}") if not query else path.count("{}") + query.count("{}")):
                # blank count doesn't match count of insert values
                raise ValueError("Unequal amount of blanks and insert values.")

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
            if status != 200:
                print("A GET request got an unexpected status code response!")
                print("Concerned URL: ", url)
                print("HTTP Status Code: ", status)
                raise Exception
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
                print("A GET request got an unexpected status code response!")
                print("Concerned URL:", url)
                print("HTTP Status Code:", status)
                raise Exception
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
