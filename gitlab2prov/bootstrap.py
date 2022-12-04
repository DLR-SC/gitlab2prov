import inspect
import logging
from typing import Type

from gitlab2prov.service_layer import handlers, messagebus, unit_of_work
from gitlab2prov.adapters.fetch import GitFetcher, GitlabFetcher, GithubFetcher


log = logging.getLogger(__name__)


def bootstrap(
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.InMemoryUnitOfWork(),
    git_fetcher: Type[GitFetcher] = GitFetcher,
    gitlab_fetcher: Type[GitlabFetcher] = GitlabFetcher,
):
    dependencies = {
        "uow": uow,
        "git_fetcher": git_fetcher,
        "gitlab_fetcher": gitlab_fetcher,
        "github_fetcher": GithubFetcher,
    }
    injected_handlers = {
        command_type: [inject_dependencies(handler, dependencies) for handler in handlers]
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
