import logging
from urllib.parse import urlsplit
from tempfile import TemporaryDirectory

from git import Repo
from gitlab import Gitlab
from prov.dot import prov_to_dot
from prov.model import ProvDocument

from gitlab2prov.domain import commands
from gitlab2prov.prov import operations
from gitlab2prov.prov import model


log = logging.getLogger(__name__)


def project_slug(url: str) -> str:
    path = urlsplit(url).path
    if path is None:
        return None
    return path.strip("/")


def gitlab_url(url: str) -> str:
    split = urlsplit(url)
    return f"{split.scheme}://{split.netloc}"


def clone_with_https_url(url: str, token: str) -> str:
    split = urlsplit(url)
    return f"https://gitlab.com:{token}@{split.netloc}/{project_slug(url)}"


def serialize_graph(graph: ProvDocument, fmt: str):
    if fmt == "dot":
        return prov_to_dot(graph)
    return graph.serialize(format=fmt)


def mine_git(cmd: commands.Fetch, uow, git_miner) -> None:
    url = clone_with_https_url(cmd.project_url, cmd.token)
    with TemporaryDirectory() as tmpdir:
        repo = Repo.clone_from(url, to_path=tmpdir)
        with uow:
            for resource in git_miner(repo).mine():
                log.debug(f"add {resource=}")
                uow.resources.add(resource)
            uow.commit()
        repo.close()


def mine_gitlab(cmd: commands.Fetch, uow, gitlab_miner) -> None:
    gl = Gitlab(gitlab_url(cmd.project_url), cmd.token)
    project = gl.projects.get(project_slug(cmd.project_url))
    with uow:
        for resource in gitlab_miner(project).mine():
            log.debug(f"add {resource=}")
            uow.resources.add(resource)
        uow.commit()


def serialize(cmd: commands.Serialize, uow) -> None:
    subgraphs = []

    for prov_model in model.MODELS:
        with uow:
            log.info(f"populate model {prov_model}")
            subgraph = prov_model(uow.resources)
        subgraphs.append(subgraph)

    graph = operations.combine(subgraphs)
    graph = operations.dedupe(graph)

    # optional operations
    if cmd.uncover_double_agents:
        graph = operations.uncover_double_agents(graph, cmd.uncover_double_agents)
        graph = operations.dedupe(graph)
    if cmd.pseudonymize:
        graph = operations.pseudonymize(graph)

    # write to stdout
    print(serialize_graph(graph, cmd.format))


HANDLERS = {
    commands.Fetch: [
        mine_git,
        mine_gitlab,
    ],
    commands.Serialize: [serialize],
}
