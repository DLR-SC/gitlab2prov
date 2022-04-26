from typing import TypeVar, Type, Optional

from gitlab2prov import bootstrap
from gitlab2prov.adapters import repository
from gitlab2prov.adapters import miners
from gitlab2prov.service_layer import unit_of_work
from gitlab2prov.service_layer import handlers


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


def FakeGitRepositoryMiner(resources):
    class FakeGitRepositoryMiner(miners.AbstractMiner):
        def __init__(self, repo):
            self.resources = resources

        def mine(self):
            return iter(self.resources)

    return FakeGitRepositoryMiner


def FakeGitlabProjectMiner(resources):
    class FakeGitlabProjectMiner(miners.AbstractMiner):
        def __init__(self, project):
            self.resources = resources

        def mine(self):
            return iter(self.resources)

    return FakeGitlabProjectMiner


def bootstrap_test_app(git_resources=None, gitlab_resources=None):
    if git_resources is None:
        git_resources = []
    if gitlab_resources is None:
        gitlab_resources = []
    return bootstrap.bootstrap(
        uow=FakeUnitOfWork(),
        git_miner=FakeGitRepositoryMiner(git_resources),
        gitlab_miner=FakeGitlabProjectMiner(gitlab_resources),
    )


class TestHelpers:
    def test_project_slug(self):
        expected_slug = "group/project"
        assert expected_slug == handlers.project_slug(
            "https://gitlab.com/group/project"
        )

    def test_gitlab_url(self):
        expected_url = "https://gitlab.com"
        assert expected_url == handlers.gitlab_url("https://gitlab.com/group/project")

    def test_clone_with_https_url(self):
        expected_url = "https://gitlab.com:TOKEN@gitlab.com/group/project"
        assert expected_url == handlers.clone_with_https_url(
            "https://gitlab.com/group/project", "TOKEN"
        )
