# Copyright (c) 2019 German Aerospace Center (DLR/SC).
# All rights reserved.
#
# This file is part of gitlab2prov.
# gitlab2prov is licensed under the terms of the MIT License.
# SPDX short Identifier: MIT
#
# You may obtain a copy of the License at:
# https://opensource.org/licenses/MIT
#
# A command line tool to extract provenance data (PROV W3C)
# from GitLab hosted repositories aswell as
# to store the extracted data in a Neo4J database.
#
# code-author: Claas de Boer <claas.deboer@dlr.de>


from __future__ import annotations

import asyncio
import collections
import urllib.parse
from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Tuple

import gl2p.ratelimiter as ratelimiter
from gl2p.helpers import chunks, url_encoded_path

BATCH_SIZE = 2000
PAGE_SIZE = 50


USERS = "users"
COMMITS = "repository/commits"
COMMIT_DIFFS = "repository/commits/{}/diff"
COMMIT_NOTES = "repository/commits/{}/discussions"
ISSUES = "issues"
ISSUE_NOTES = "issues/{}/notes"
ISSUE_LABELS = "issues/{}/resource_label_events"
ISSUE_AWARDS = "issues/{}/award_emoji"
ISSUE_NOTE_AWARDS = "issues/{}/notes/{}/award_emoji"
MERGE_REQUESTS = "merge_requests"
MERGE_REQUEST_LABELS = "merge_requests/{}/resource_label_events"
MERGE_REQUEST_AWARDS = "merge_requests/{}/award_emoji"
MERGE_REQUEST_NOTES = "merge_requests/{}/notes"
MERGE_REQUEST_NOTE_AWARDS = "merge_requests/{}/notes/{}/award_emoji"


def cache_result(func) -> Callable[[Any], Coroutine[Any, Any, Any]]:
    """Decorator that stores method return values in a self._cache.

    Returns:
        Callable: Wrapped method.
    """

    async def wrapped(self) -> Any:
        """Wrapper caching the value of the wrapped function."""

        res = await func(self)
        if not self._cache:
            self._cache = {}

        self._cache[func.__name__] = res
        return res

    return wrapped


async def gather(coroutines_or_tasks, batch_size):
    """Wrapping one thing at a time."""

    res = []

    for chunk in chunks(coroutines_or_tasks, batch_size):
        res.extend(await asyncio.gather(*chunk))

    return res


@dataclass
class ProjectWrapper:
    """Asynchronous rate limited gitlab project API wrapper."""

    project_url: InitVar[str]
    token: str
    rate: int = 10

    url: str = ""
    project_id: str = ""

    _cache: Dict[str, Any] = field(default_factory=dict)
    __session: ratelimiter.Session = None

    def __post_init__(self, project_url: str):
        """Extract GitLab url and project id from project url."""

        self.project_id = url_encoded_path(project_url)
        scheme, netloc, *_ = urllib.parse.urlparse(project_url)
        self.url = f"{scheme}://{netloc}/api/v4/projects/{self.project_id}"

    async def __aenter__(self):
        """Init self.__session on entering context."""

        headers = {"Private-Token": self.token}
        self.__session = ratelimiter.Session(rate=self.rate, headers=headers)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session upon leaving context."""

        await self.__session.close()

    async def _first_page(self, url: str) -> Tuple[Any, int]:
        """Coroutine that performs a GET request to the first page of target *url*.

        Returns content as json aswell as the number
        of pages that the content spreads across.
        """

        # TODO: retry on 429 TOO MANY REQUESTS after specified amount of time

        params = {"per_page": PAGE_SIZE}
        async with await self.__session.get(url, params=params) as resp:

            json = await resp.json()
            x_total_pages = int(resp.headers.get("x-total-pages", 0))

            return json, x_total_pages

    async def _single_page(self, url: str, page_number: int) -> Any:
        """Coroutine that performs a GET request to a specific page of target *url*."""

        params = {"per_page": PAGE_SIZE, "page": page_number}
        async with await self.__session.get(url, params=params) as resp:
            return await resp.json()

    def _format_urls(self, path: str, inserts: List[Any] = []) -> List[str]:
        """Build urls that are going to be used in GET requests."""

        urls = []

        if not inserts:
            return [f"{self.url}/{path}"]

        for tpl in inserts:
            if isinstance(tpl, tuple):
                fmt = path.format(*tpl)
            else:
                fmt = path.format(tpl)
            urls.append(f"{self.url}/{fmt}")

        return urls

    async def request(self, path, inserts=[]):
        """Perform GET requests for all built urls asynchronously in batches."""

        urls = self._format_urls(path, inserts)

        first_pages = [self._first_page(url) for url in urls]
        first_pages = await gather(first_pages, BATCH_SIZE)

        remaining = [
            self._single_page(url, page_number=n)
            for url, (_, x_total_pages) in zip(urls, first_pages)
            for n in range(2, x_total_pages + 1)
        ]

        remaining = collections.deque(await gather(remaining, BATCH_SIZE))

        results = []

        for (page, x_total_pages) in first_pages:

            for _ in range(2, x_total_pages + 1):
                page.extend(remaining.popleft())

            results.append(page)

        return results

    @cache_result
    async def users(self) -> Any:
        """Get all users of the wrapped project."""

        users = []

        for sublist in await self.request(USERS):
            for user in sublist:
                users.append(user)

        return users

    @cache_result
    async def commits(self):
        """Get all commits of the wrapped project."""

        commits = []

        for sublist in await self.request(COMMITS):
            for commit in sublist:
                commits.append(commit)

        return commits

    async def commit_diffs(self):
        """Get all diffs for all commits of the wrapped project."""

        commits = self._cache.get("commits")

        if not commits:
            commits = self.commits()

        if not commits:
            return []

        inserts = [c.get("id") for c in commits]
        return await self.request(COMMIT_DIFFS, inserts)

    @cache_result
    async def commit_notes(self):
        """Retrieve notes that reside on commits of the wrapped project.

        A note on commit notes:

        As of right now (Jan, 2020) there is no API endpoint to retrieve
        notes that are attached to GitLab commit resources. Rather you
        have to get "discussions" which organize notes in threads.

        This is inconsistent with the model that GitLab provides for other
        resources such as merge requests or issues. Additionally, though you
        can award emoji to notes of commit resources, there is no way
        to retrieve the awarded emoji.

        This - considering that the analysis of interaction, communication
        and collaboration on git-hosting platforms thrives of each retrievable
        resource - is sad.
        """

        commits = self._cache.get("commits")

        if not commits:
            commits = await self.commits()

        if not commits:
            return []

        inserts = [c.get("id") for c in commits]
        commits = await self.request(COMMIT_NOTES, inserts)

        return [
            [note for discussion in commit for note in discussion.get("notes", [])]
            for commit in commits
        ]

    @cache_result
    async def issues(self):
        """Get all issues of the wrapped project."""

        issues = []

        for sublist in await self.request(ISSUES):
            for issue in sublist:
                issues.append(issue)

        return issues

    @cache_result
    async def issue_notes(self):
        """Get all notes of all issues of the wrapped project."""

        issues = self._cache.get("issues")

        if not issues:
            issues = self.issues()

        if not issues:
            return []

        inserts = [i.get("iid") for i in issues]
        notes = await self.request(ISSUE_NOTES, inserts)

        return notes

    async def issue_label_events(self):
        """Get all issue label events for all issues of the wrapped project."""

        issues = self._cache.get("issues")

        if not issues:
            issues = self.issues()

        if not issues:
            return []

        inserts = [i.get("iid") for i in issues]
        label_events = await self.request(ISSUE_LABELS, inserts)

        return label_events

    async def issue_award_emoji(self):
        """Get all award emoji of all issues of the wrapped project."""

        issues = self._cache.get("issues")

        if not issues:
            issues = self.issues()

        if not issues:
            return []

        inserts = [i.get("iid") for i in issues]
        awards = await self.request(ISSUE_AWARDS, inserts)

        return awards

    async def issue_note_award_emoji(self):
        """Get all award emoji of all notes of all issues of the wrapped project."""

        issue_notes = self._cache.get("issue_notes")

        if not issue_notes:
            issue_notes = self.issue_notes()

        if not issue_notes:
            return []

        inserts = [
            (n.get("noteable_iid"), n.get("id")) for notes in issue_notes for n in notes
        ]

        return await self.request(ISSUE_NOTE_AWARDS, inserts)

    @cache_result
    async def merge_requests(self):
        """Get all merge requests of the wrapped project."""

        merge_requests = []

        for sublist in await self.request(MERGE_REQUESTS):
            for mr in sublist:
                merge_requests.append(mr)

        return merge_requests

    @cache_result
    async def merge_request_notes(self):
        """Get all notes of all merge requests of the wrapped project."""

        merge_requests = self._cache.get("merge_requests")

        if not merge_requests:
            merge_requests = await self.merge_requests()

        if not merge_requests:
            return []

        inserts = [mr.get("iid") for mr in merge_requests]
        mr_notes = await self.request(MERGE_REQUEST_NOTES, inserts)

        return mr_notes

    async def merge_request_label_events(self):
        """Get all label events for all merge requests of the wrapped project."""

        merge_requests = self._cache.get("merge_requests")

        if not merge_requests:
            merge_requests = await self.merge_requests()

        if not merge_requests:
            return []

        inserts = [mr.get("iid") for mr in merge_requests]
        return await self.request(MERGE_REQUEST_LABELS, inserts)

    async def merge_request_award_emoji(self):
        """Get all award emoji of all merge requests of the wrapped project."""

        merge_requests = self._cache.get("merge_requests")

        if not merge_requests:
            merge_requests = await self.merge_requests()

        if not merge_requests:
            return []

        inserts = [mr.get("iid") for mr in merge_requests]
        return await self.request(MERGE_REQUEST_AWARDS, inserts)

    async def merge_request_note_award_emoji(self):
        """Get all award emoji of all notes of all merge requests of the wrapped project."""

        merge_request_notes = self._cache.get("merge_request_notes")

        if not merge_request_notes:
            merge_request_notes = await self.merge_request_notes()

        if not merge_request_notes:
            return []

        inserts = [
            (note.get("noteable_iid"), note.get("id"))
            for mr in merge_request_notes
            for note in mr
            if not note.get("system")
        ]

        return await self.request(MERGE_REQUEST_NOTE_AWARDS, inserts)
