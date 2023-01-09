from gitlab2prov.adapters.fetch._git import GitFetcher
from gitlab2prov.adapters.fetch._gitlab import GitlabFetcher
from gitlab2prov.adapters.fetch._github import GithubFetcher


class FetcherFactory:
    @staticmethod 
    def factory(url: str):
        if "github" in url:
            return GithubFetcher
        if "gitlab" in url:
            return GitlabFetcher
        raise ValueError(f"can't derive fetcher for unknown url {url=}")
    