import uuid
from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvRole


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_user():
    return objects.User(
        name=f"user-name-{random_suffix()}",
        email=f"user-email-{random_suffix()}",
        gitlab_username=f"gitlab-user-name-{random_suffix()}",
        gitlab_id=f"gitlab-user-id-{random_suffix()}",
        prov_role=ProvRole.AUTHOR,
    )
