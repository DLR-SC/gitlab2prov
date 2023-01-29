from urllib.parse import urlsplit
from dataclasses import dataclass


@dataclass
class ProjectUrl:
    url: str

    @property
    def slug(self) -> str:
        if path := urlsplit(self.url).path:
            owner, project = (s for s in path.split("/") if s)
            return f"{owner}/{project}"
        return None

    @property
    def instance(self) -> str:
        return f"{self.scheme}://{self.netloc}"

    @property
    def netloc(self):
        return urlsplit(self.url).netloc

    @property
    def scheme(self):
        return "https"

    def clone_url(self, platform: str, token: str | None = None, method: str = "https"):
        urls = {
            "gitlab": f"{self.instance}:{token}@{self.netloc}/{self.slug}",
            "github": f"{self.scheme}://{token}@{self.netloc}/{self.slug}.git",
        }
        return urls.get(platform)


@dataclass
class GitlabProjectUrl(ProjectUrl):
    def clone_url(self, token: str | None = None, method: str = "https"):
        return super().clone_url("gitlab", token, method)


@dataclass
class GithubProjectUrl(ProjectUrl):
    def clone_url(self, token: str | None = None, method: str = "https"):
        return super().clone_url("github", token, method)
