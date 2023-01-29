import logging

from gitlab2prov.domain import commands
from gitlab2prov.prov import model, operations
from prov.model import ProvDocument


log = logging.getLogger(__name__)


def fetch_git(cmd: commands.Fetch, uow, git_fetcher) -> None:
    with git_fetcher as fetcher:
        fetcher.do_clone(cmd.url, cmd.token)
        with uow:
            for resource in fetcher.fetch_all():
                log.info(f"add {resource=}")
                uow.resources[cmd.url].add(resource)
        uow.commit()


def fetch_githosted(cmd: commands.Fetch, uow, githosted_fetcher) -> None:
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
        provenance = prov_model(uow.resources[cmd.url])
        document = operations.combine(document, provenance)
        document = operations.dedupe(document)
    return document


def normalize(cmd: commands.Normalize):
    if cmd.no_duplicates:
        cmd.document = operations.dedupe(cmd.doc)
    if cmd.use_pseudonyms:
        cmd.document = operations.pseudonymize(cmd.doc)
    return cmd.document


def combine(cmd: commands.Combine):
    return operations.combine(*cmd.documents)


def document2file(cmd: commands.Document2File):
    return operations.serialize(cmd.document, cmd.filename, cmd.format)


def file2document(cmd: commands.File2Document):
    return operations.deserialize(cmd.source, cmd.content, cmd.format)


def statistics(cmd: commands.Statistics):
    return operations.stats(cmd.document, cmd.resolution, cmd.format)


HANDLERS = {
    commands.Fetch: [
        fetch_git,
        fetch_githosted,
    ],
    commands.Serialize: [serialize],
    commands.Document2File: [document2file],
    commands.File2Document: [file2document],
    commands.Combine: [combine],
    commands.Normalize: [normalize],
    commands.Statistics: [statistics],
}
