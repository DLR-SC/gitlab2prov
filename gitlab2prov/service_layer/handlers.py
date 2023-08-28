import logging

from gitlab2prov.domain import commands
from gitlab2prov.prov import model, operations
from prov.model import ProvDocument


log = logging.getLogger(__name__)


def fetch_git(cmd: commands.Fetch, uow, git_fetcher) -> None:
    log.info(f"fetch {cmd=}")
    with git_fetcher as fetcher:
        fetcher.do_clone(cmd.url, cmd.token)
        with uow:
            for resource in fetcher.fetch_all():
                log.info(f"add {resource=}")
                uow.resources[cmd.url].add(resource)
        uow.commit()


def fetch_githosted(cmd: commands.Fetch, uow, githosted_fetcher) -> None:
    log.info(f"fetch {cmd=}")
    fetcher = githosted_fetcher(cmd.token, cmd.url)
    with uow:
        for resource in fetcher.fetch_all():
            log.info(f"add {resource=}")
            uow.resources[cmd.url].add(resource)
        uow.commit()


def serialize(cmd: commands.Serialize, uow) -> ProvDocument:
    log.info(f"serialize graph consisting of {model.MODELS=}")
    document = ProvDocument()
    for prov_model in model.MODELS:
        log.info(f"populate {prov_model=}")
        provenance = prov_model(uow.resources[cmd.url])
        document = operations.combine(document, provenance)
        document = operations.dedupe(document)
    return document


def transform(cmd: commands.Transform):
    log.info(f"transform {cmd=}")
    if cmd.remove_duplicates:
        cmd.document = operations.dedupe(cmd.doc)
    if cmd.use_pseudonyms:
        cmd.document = operations.pseudonymize(cmd.doc)
    if cmd.merge_aliased_agents:
        cmd.document = operations.merge_duplicated_agents(cmd.doc, cmd.merge_aliased_agents)
    return cmd.document


def combine(cmd: commands.Combine):
    log.info(f"combine {cmd=}")
    return operations.combine(*cmd.documents)


def write_file(cmd: commands.Write):
    log.info(f"write {cmd=}")
    return operations.write_provenance_file(cmd.document, cmd.filename, cmd.format)


def read_file(cmd: commands.Read):
    log.info(f"read {cmd=}")
    return operations.read_provenance_file(cmd.filename)


def statistics(cmd: commands.Statistics):
    log.info(f"statistics {cmd=}")
    return operations.stats(cmd.document, cmd.resolution, cmd.format)


HANDLERS = {
    commands.Fetch: [
        fetch_git,
        fetch_githosted,
    ],
    commands.Serialize: [serialize],
    commands.Read: [read_file],
    commands.Write: [write_file],
    commands.Combine: [combine],
    commands.Transform: [transform],
    commands.Statistics: [statistics],
}
