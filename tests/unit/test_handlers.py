from typing import TypeVar, Type, Optional
from pathlib import Path

from gitlab2prov import bootstrap
from gitlab2prov.adapters import repository
from gitlab2prov.adapters import miners
from gitlab2prov.service_layer import unit_of_work
from gitlab2prov.domain import commands, objects

import tests.random_refs as random_refs


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


class FakeGitRepositoryMiner(miners.AbstractMiner):
    def __init__(self, resources):
        self.resources = resources

    def mine(self):
        return iter(self.resources)


class FakeGitlabProjectMiner(miners.AbstractMiner):
    def __init__(self, resources):
        self.resources = resources

    def mine(self):
        return iter(self.resources)


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


class TestCloneGitRepository:
    def test_https_clone_url_composition(self, mocker):
        repo = mocker.patch("git.Repo.clone_from")
        netloc, path = "gitlab.com", "/group/project"
        bus = bootstrap_test_app()
        bus.handle(commands.Fetch(f"https://{netloc}{path}", "token", Path("gitdir")))
        expected_url = f"https://gitlab.com:token@gitlab.com/group/project"
        expected_path = Path("gitdir/project")
        repo.assert_called_once_with(expected_url, to_path=expected_path, quiet=True)


class TestMineGit:
    def test_adds(self, mocker):
        mocker.patch("git.Repo")
        user = random_refs.random_user()
        bus = bootstrap_test_app(git_resources=[user])
        bus.handle(commands.Fetch("https://gitlab.com/group/project", "token"))
        user = bus.uow.resources.get(objects.User, name=user.name)
        assert user

    def test_commits(self, mocker):
        mocker.patch("git.Repo")
        user = random_refs.random_user()
        bus = bootstrap_test_app(git_resources=[user])
        bus.handle(commands.Fetch("https://gitlab.com/group/project", "token"))
        assert bus.uow.committed

    def test_errors_for_invalid_repository_file_path(self, mocker):
        mocker.patch("git.Repo")
        bus = bootstrap_test_app()
        bus.handle(commands.Fetch("https://gitlab.com/group/project", "token"))
        assert True


class TestMineGitlab:
    def test_adds(self, mocker):
        mocker.patch("git.Repo")
        user = random_refs.random_user()
        bus = bootstrap_test_app(gitlab_resources=[user])
        bus.handle(commands.Fetch("https://gitlab.com/group/project", "token"))
        user = bus.uow.resources.get(objects.User, name=user.name)
        assert user

    def test_commits(self, mocker):
        mocker.patch("git.Repo")
        user = random_refs.random_user()
        bus = bootstrap_test_app(gitlab_resources=[user])
        bus.handle(commands.Fetch("https://gitlab.com/group/project", "token"))
        assert bus.uow.committed

    def test_errors_for_invalid_url(self, mocker):
        mocker.patch("git.Repo")
        bus = bootstrap_test_app()
        bus.handle(commands.Fetch("https://gitlab.com/group/project", "token"))
        assert True
