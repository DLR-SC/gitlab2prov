import pytest
from gitlab2prov.adapters.repository import InMemoryRepository


class TestInMemoryRepository:


    def test_add_resource(self, random_user):
        repo = InMemoryRepository()
        resource = random_user 
        repo.add(resource)
        assert len(repo.repo[type(resource)]) == 1
        assert repo.repo[type(resource)][0] == resource

    def test_get_resource_existing(self, random_user):
        repo = InMemoryRepository()
        resource = random_user
        repo.add(resource)
        retrieved_resource = repo.get(type(resource))
        assert retrieved_resource == resource

    def test_get_resource_non_existing(self, random_user):
        repo = InMemoryRepository()
        retrieved_resource = repo.get(type(random_user))
        assert retrieved_resource is None

    @pytest.mark.fixt_data(2)
    def test_get_resource_with_filters_existing(self, n_random_users):
        repo = InMemoryRepository()
        resource1 = n_random_users[0]
        resource2 = n_random_users[1]
        repo.add(resource1)
        repo.add(resource2)
        retrieved_resource = repo.get(type(resource1), email=resource1.email, name=resource1.name)
        assert retrieved_resource == resource1

    def test_get_resource_with_filters_non_existing(self, random_user):
        repo = InMemoryRepository()
        resource = random_user
        repo.add(resource)
        retrieved_resource = repo.get(type(resource), name="...", email="...")
        assert retrieved_resource is None

    def test_get_resource_throws_attribute_error_for_non_existing_attributes(self, random_user):
        repo = InMemoryRepository()
        resource = random_user
        repo.add(resource)
        try:
            repo.get(type(resource), non_existing_attribute="...")
        except AttributeError:
            assert True
        else:
            assert False

    @pytest.mark.fixt_data(2)
    def test_list_all_resources(self, n_random_users):
        repo = InMemoryRepository()
        resource1 = n_random_users[0]
        resource2 = n_random_users[1]
        repo.add(resource1)
        repo.add(resource2)
        retrieved_resources = repo.list_all(type(resource1))
        assert len(retrieved_resources) == 2
        assert resource1 in retrieved_resources
        assert resource2 in retrieved_resources

    pytest.mark.fixt_data(2)
    def test_list_all_resources_with_filters_existing(self, n_random_users):
        repo = InMemoryRepository()
        resource1 = n_random_users[0]
        resource2 = n_random_users[1]
        repo.add(resource1)
        repo.add(resource2)
        retrieved_resources = repo.list_all(
            type(resource1), name=resource1.name, email=resource1.email
        )
        assert len(retrieved_resources) == 1
        assert resource1 in retrieved_resources

    @pytest.mark.fixt_data(2)
    def test_list_all_resources_with_filters_non_existing(self, n_random_users):
        repo = InMemoryRepository()
        resource1 = n_random_users[0]
        resource2 = n_random_users[1]
        repo.add(resource1)
        repo.add(resource2)
        retrieved_resources = repo.list_all(type(resource1), name="...", email="...")
        assert len(retrieved_resources) == 0

    def test_list_all_resources_throws_attribute_error_for_non_existing_attributes(self, random_user):
        repo = InMemoryRepository()
        resource1 = random_user
        repo.add(resource1)
        try:
            repo.list_all(type(resource1), non_existing_attribute="...")
        except AttributeError:
            assert True
        else:
            assert False
