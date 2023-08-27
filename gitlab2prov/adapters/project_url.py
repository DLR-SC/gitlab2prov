from urllib.parse import urlsplit
from dataclasses import dataclass


@dataclass
class ProjectUrl:
    url: str
    scheme: str = "https"

    def __post_init__(self):
        parsed_url = urlsplit(self.url)
        self.url_path = parsed_url.path
        self.netloc = parsed_url.netloc

    @property
    def slug(self) -> str:
        if self.url_path:
            *owner, project = self.url_path.split("/")
            owner = "/".join(owner)[1:]
            return f"{owner}/{project}"
        return ""

    @property
    def instance(self) -> str:
        return f"{self.scheme}://{self.netloc}"

    def clone_url(self, platform: str, token: str = "") -> str:
        platform_urls = {
            "gitlab": f"{self.instance}:{token}@{self.netloc}/{self.slug}",
            "github": f"{self.scheme}://{token}@{self.netloc}/{self.slug}.git",
        }
        return platform_urls.get(platform, "")


@dataclass
class GitlabProjectUrl(ProjectUrl):
    def clone_url(self, token: str = ""):
        return super().clone_url("gitlab", token)


@dataclass
class GithubProjectUrl(ProjectUrl):
    def clone_url(self, token: str = ""):
        return super().clone_url("github", token)
