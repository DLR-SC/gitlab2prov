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


def fetch_gitlab(cmd: commands.Fetch, uow, gitlab_fetcher, github_fetcher) -> None:
    fetcher = gitlab_fetcher() if "gitlab" in cmd.url else github_fetcher()
    fetcher.do_login(cmd.url, cmd.token)
    with uow:
        for resource in fetcher.fetch_gitlab():
            log.info(f"add {resource=}")
            uow.resources.add(resource)
        uow.commit()


def reset(cmd: commands.Reset, uow):
    log.info(f"reset repository {uow.resources=}")
    uow.reset()


def serialize(cmd: commands.Serialize, uow) -> ProvDocument:
    log.info(f"serialize graph consisting of {model.MODELS=}")
    graph = operations.combine(prov_model(uow.resources) for prov_model in model.MODELS)
    graph = operations.dedupe(graph)
    return graph


HANDLERS = {
    commands.Fetch: [
        fetch_git,
        fetch_gitlab,
    ],
    commands.Reset: [reset],
    commands.Serialize: [serialize],
}
