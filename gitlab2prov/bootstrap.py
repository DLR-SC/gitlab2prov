import inspect
import logging

from gitlab2prov.service_layer import handlers, messagebus, unit_of_work

from gitlab2prov.adapters.git import GitFetcher
from gitlab2prov.adapters.lab import GitlabFetcher
from gitlab2prov.adapters.hub import GithubFetcher
from gitlab2prov.adapters.project_url import GithubProjectUrl, GitlabProjectUrl


log = logging.getLogger(__name__)


def bootstrap(
    platform: str,
    uow: unit_of_work.UnitOfWork = unit_of_work.InMemoryUnitOfWork(),
    git_fetcher: type[GitFetcher] = GitFetcher,
    gitlab_fetcher: type[GitlabFetcher] = GitlabFetcher,
    github_fetcher: type[GithubFetcher] = GithubFetcher,
    github_url: type[GithubProjectUrl] = GithubProjectUrl,
    gitlab_url: type[GitlabProjectUrl] = GitlabProjectUrl,
):
    dependencies = {
        "uow": uow,
        "git_fetcher": git_fetcher(gitlab_url if platform == "gitlab" else github_url),
        "githosted_fetcher": gitlab_fetcher if platform == "gitlab" else github_fetcher,
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
