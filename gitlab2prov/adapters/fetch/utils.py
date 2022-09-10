from urllib.parse import urlsplit


def project_slug(url: str) -> str:
    path = urlsplit(url).path
    if path is None:
        return None
    return path.strip("/")


def gitlab_url(url: str) -> str:
    split = urlsplit(url)
    return f"{split.scheme}://{split.netloc}"


def clone_over_https_url(url: str, token: str) -> str:
    split = urlsplit(url)
    return f"https://gitlab.com:{token}@{split.netloc}/{project_slug(url)}"
