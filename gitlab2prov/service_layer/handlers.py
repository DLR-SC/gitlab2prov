import logging

from gitlab2prov.domain import commands
from gitlab2prov.prov import model, operations
from prov.model import ProvDocument


log = logging.getLogger(__name__)


def fetch_git(cmd: commands.Fetch, uow, git_fetcher) -> None:
    with git_fetcher(cmd.url, cmd.token) as fetcher:
        fetcher.do_clone()
        with uow:
            for resource in fetcher.fetch_git():
                log.info(f"add {resource=}")
                uow.resources.add(resource)
        uow.commit()


def fetch_gitlab(cmd: commands.Fetch, uow, gitlab_fetcher) -> None:
    fetcher = gitlab_fetcher(cmd.url, cmd.token)
    fetcher.do_login()
    with uow:
        for resource in fetcher.fetch_gitlab():
            log.info(f"add {resource=}")
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

    if cmd.out is not None:
        with open(f"{strip_file_extension(cmd.out)}.{cmd.format}", "w") as f:
            print(serialize_graph(graph, cmd.format), file=f)
        return

    print(serialize_graph(graph, cmd.format))


HANDLERS = {
    commands.Fetch: [
        mine_git,
        mine_gitlab,
    ],
    commands.Serialize: [serialize],
}
