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


def fetch_githosted(cmd: commands.Fetch, uow, fetcher_factory) -> None:
    fetcher = fetcher_factory.factory(cmd.url)
    log.info("choose fetcher {fetcher=} for {cmd.url=}")
    fetcher = fetcher(cmd.token, cmd.url)
    with uow:
        for resource in fetcher.fetch_all():
            log.info(f"add {resource=}")
            uow.resources.add(resource)
        uow.commit()


def reset(cmd: commands.Reset, uow):
    log.info(f"reset repository {uow.resources=}")
    uow.reset()


def serialize(cmd: commands.Serialize, uow) -> ProvDocument:
    log.info(f"serialize graph consisting of {model.MODELS=}")
    document = ProvDocument()
    for prov_model in model.MODELS:
        provenance = prov_model(uow.resources)
        document = operations.combine(document, provenance)
        document = operations.dedupe(document)
    return document


HANDLERS = {
    commands.Fetch: [
        fetch_git,
        fetch_githosted,
    ],
    commands.Reset: [reset],
    commands.Serialize: [serialize],
}
