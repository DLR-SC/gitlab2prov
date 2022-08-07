from typing import TypeVar, Type, Optional

from gitlab2prov import bootstrap
from gitlab2prov.adapters import repository
from gitlab2prov.service_layer import unit_of_work


R = TypeVar("R")


class FakeRepository(repository.AbstractRepository):
    def __init__(self, resources: R):
        self._resources = set(resources)

    def _add(self, resource: R):
        self._resources.add(resource)

    def _get(self, resource_type: Type[R], **filters) -> Optional[R]:
        return next(
            (
                r
                for r in self._resources
                if all(getattr(r, key) == val for key, val in filters.items())
            )
        )

    def _list_all(self, resource_type: Type[R], **filters) -> list[R]:
        return [
            r
            for r in self._resources
            if all(getattr(r, key) == val for key, val in filters.items())
        ]


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.resources = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


def FakeGitFetcher(resources):
    class FakeGitRepositoryMiner:
        def __init__(self, url, token):
            self.resources = resources

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def do_clone(self):
            pass

        def fetch_git(self):
            return iter(self.resources)

    return FakeGitRepositoryMiner


def FakeGitlabFetcher(resources):
    class FakeGitlabFetcher:
        def __init__(self, url, token):
            self.resources = resources

        def do_login(self):
            pass

        def fetch_gitlab(self):
            return iter(self.resources)

    return FakeGitlabFetcher


def bootstrap_test_app(git_resources=None, gitlab_resources=None):
    if git_resources is None:
        git_resources = []
    if gitlab_resources is None:
        gitlab_resources = []
    return bootstrap.bootstrap(
        uow=FakeUnitOfWork(),
        git_fetcher=FakeGitFetcher(git_resources),
        gitlab_fetcher=FakeGitlabFetcher(gitlab_resources),
    )


class TestHandlers:
    pass
