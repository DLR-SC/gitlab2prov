import random
import string
import pytest

from gitlab2prov.domain.objects import User


def generate_random_user():
    name = "".join(random.choice(string.ascii_letters) for _ in range(6))
    email = f"{name}@example.com"
    gitlab_username = "".join(random.choice(string.ascii_lowercase) for _ in range(6))
    github_username = "".join(random.choice(string.ascii_lowercase) for _ in range(6))
    gitlab_id = str(random.randint(1000, 9999))
    github_id = str(random.randint(1000, 9999))
    prov_role = random.choice(["admin", "user", "guest", None])
    return User(
        name=name,
        email=email,
        gitlab_username=gitlab_username,
        github_username=github_username,
        gitlab_id=gitlab_id,
        github_id=github_id,
        prov_role=prov_role,
    )
    

@pytest.fixture
def random_user() -> User:
    return generate_random_user()


@pytest.fixture
def n_random_users(request) -> list[User]:
    marker = request.node.get_closest_marker("fixt_data")
    n = 10 if marker is None else marker.args[0]
    return [generate_random_user() for _ in range(n)]
