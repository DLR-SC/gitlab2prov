import inspect
import logging
import typing

from gitlab2prov.service_layer import handlers, messagebus, unit_of_work
from gitlab2prov.adapters import miners


log = logging.getLogger(__name__)


def bootstrap(
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.InMemoryUnitOfWork(),
    git_miner: typing.Type[miners.AbstractMiner] = miners.GitRepositoryMiner,
    gitlab_miner: typing.Type[miners.AbstractMiner] = miners.GitlabProjectMiner,
):
    dependencies = {
        "uow": uow,
        "git_miner": git_miner,
        "gitlab_miner": gitlab_miner,
    }
    injected_handlers = {
        command_type: [
            inject_dependencies(handler, dependencies) for handler in handlers
        ]
        for command_type, handlers in handlers.HANDLERS.items()
    }

    return messagebus.MessageBus(uow, handlers=injected_handlers)


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    dependencies = {
        name: dependency for name, dependency in dependencies.items() if name in params
    }
    for name, dep in dependencies.items():
        log.debug(f"inject dependency {dep} into handler {handler} as param {name}")
    return lambda cmd: handler(cmd, **dependencies)
