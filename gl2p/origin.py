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


from collections import namedtuple, defaultdict, deque
from urllib.parse import urlparse, urlunparse
from functools import reduce
from time import time
from gitlab import Gitlab
from gl2p.config import CONFIG
from gl2p.commons import Repository, File, NameTable, FileStatus
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
        commits = project.commits.list(all=True)

        urls = []
        parsed = urlparse(CONFIG["GITLAB"]["url"])._asdict()
        for commit in commits:
            path = "/api/v4/projects/{}/repository/commits/{}/diff"
            parsed["path"] = path.format(pathify(purl), commit.id)
            urls.append(urlunparse(tuple(parsed.values())))

        async_client = RateLimitedAsyncRequestHandler()
        diffs = async_client.get_batch(urls)

        disc = {commit.id: commit.discussions.list(all=True) for commit in commits}
        for sha, discussion in disc.items():
            print(sha, " -- ", discussion)
            for d in discussion:
                for note in d.attributes.get("notes"):
                    if note.get("system"):
                        print(note)

        data = namedtuple("data", "path commits diffs issues")
        path = urlparse(purl).path
        issues = []
        self.data = data(path, commits, diffs, issues)

    def process(self):
        nametables = {}
        commits = {c.id: c for c in self.data.commits}
        diffs = {c.id: d for c, d in zip(self.data.commits, self.data.diffs)}
        
        children = defaultdict(set)
        for commit in commits.values():
            for sha in commit.parent_ids:
                children[sha].add(commit.id)

        root = self.data.commits[-1].attributes.get("id")
        queue = deque([root])
        visited = set()
        
        t = time()
        while queue:
            sha = queue.popleft()
            commit = commits.get(sha)
            if sha in visited:
                continue
            if all([(pid in nametables) for pid in commit.parent_ids]):
                # all previous nametables cached
                if sha == root:
                    # NT(0) = δ({})
                    # diff applied on empty nametable
                    nametables[sha] = NameTable().delta(diffs.get(sha))
                    visited.add(sha)
                    queue.extend(children.get(sha, []))
                    continue
                # combination of previous nametables, apply diff before union
                # NT(n) = δ(NT(n-1)) + δ(NT(n-2)) + ... δ(NT(0))
                nts = []
                for pid in commit.parent_ids:
                    nts.append(nametables.get(pid).delta(diffs.get(sha)))
                nametables[sha] = reduce(lambda nt1, nt2: nt1+nt2, nts)
                visited.add(sha)
            else:
                # not all cached, wait in queue
                queue.append(sha)
                continue
            for child in children.get(sha, []):
                if child not in visited:
                    queue.append(child)
        print(f"Created nametables in : {time()-t}")
        
        # add files to commits
        commits = []
        for commit, diff in zip(self.data.commits, self.data.diffs):
            files = []
            for entry in diff:
                if entry["new_file"]: 
                    status = FileStatus.ADDED
                elif entry["deleted_file"]:
                    status = FileStatus.DELETED
                else:
                    status = FileStatus.MODIFIED
                f = File(commit.id, entry["old_path"], entry["new_path"], status)
                files.append(f)
            commit._update_attrs({"files": files})
            commits.append(commit)

        return Repository(self.data.path, commits, self.data.issues, nametables)
