from urllib.parse import urlsplit


def project_slug(url: str) -> str:
    if path := urlsplit(url).path:
        owner, project = (s for s in path.split("/") if s)
        return f"{owner}/{project}"
    return None


def instance_url(url: str) -> str:
    split = urlsplit(url)
    return f"{split.scheme}://{split.netloc}"


def clone_over_https_url(url: str, token: str, platform: str = "gitlab") -> str:
    split = urlsplit(url)
    if platform == "gitlab":
        return f"https://gitlab.com:{token}@{split.netloc}/{project_slug(url)}"
    if platform == "github":
        return f"https://{token}@{split.netloc}/{project_slug(url)}.git"
