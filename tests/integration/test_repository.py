from datetime import datetime, timedelta

from gitlab2prov.adapters import repository
from gitlab2prov.domain import objects


today = datetime.now()
tomorrow = today + timedelta(days=1)
yesterday = today - timedelta(days=1)


class TestInMemoryRepository:
    def test_get(self):
        repo = repository.InMemoryRepository()
        u1 = objects.User(name="u1", email="e1", prov_role="r1")
        u2 = objects.User(name="u2", email="e2", prov_role="r2")
        repo.add(u1)
        repo.add(u2)
        assert repo.get(objects.User, name="u1") == u1
        assert repo.get(objects.User, name="u2") == u2

    def test_get_returns_none_if_repository_is_empty(self):
        repo = repository.InMemoryRepository()
        assert repo.get(objects.User, name="name") == None

    def test_list_all(self):
        repo = repository.InMemoryRepository()
        u1 = objects.User(name="u1", email="e1", prov_role="r1")
        u2 = objects.User(name="u2", email="e2", prov_role="r1")
        repo.add(u1)
        repo.add(u2)
        assert repo.list_all(objects.User, name="u1") == [u1]
        assert repo.list_all(objects.User, name="u2") == [u2]
        assert repo.list_all(objects.User, prov_role="r1") == [u1, u2]

    def test_list_all_returns_empty_list_if_repository_is_empty(self):
        repo = repository.InMemoryRepository()
        assert repo.list_all(objects.User, name="name") == []
