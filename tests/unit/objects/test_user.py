from gitlab2prov.domain.objects import User
from gitlab2prov.domain.constants import ProvType


class TestUser:
    # Test cases for User class
    def test_user_creation(self):
        # Test User creation with valid inputs
        user = User(name="John Doe", email="johndoe@example.com")
        assert user.name == "John Doe"
        assert user.email == "johndoe@example.com"
        assert user.gitlab_username is None
        assert user.github_username is None
        assert user.gitlab_id is None
        assert user.github_id is None
        assert user.prov_role is None

        # Test User creation with optional parameters
        user = User(
            name="Jane Smith",
            email="janesmith@example.com",
            gitlab_username="janesmith",
            github_username="janesmith",
            gitlab_id="123",
            github_id="456",
            prov_role="developer",
        )
        assert user.name == "Jane Smith"
        assert user.email == "janesmith@example.com"
        assert user.gitlab_username == "janesmith"
        assert user.github_username == "janesmith"
        assert user.gitlab_id == "123"
        assert user.github_id == "456"
        assert user.prov_role == "developer"

    def test_user_post_init(self):
        # Test __post_init__() method with lowercase email
        user = User(name="John Doe", email="JohnDoe@example.com")
        assert user.email == "johndoe@example.com"

        # Test __post_init__() method with None email
        user = User(name="Jane Smith", email=None)
        assert user.email is None

    def test_user_identifier(self):
        # Test identifier property
        user = User(name="John Doe", email="johndoe@example.com")
        assert user.identifier.localpart == "User?name=John Doe&email=johndoe@example.com"

    def test_user_to_prov_element(self):
        # Test to_prov_element() method with minimum attributes
        user = User(name="John Doe", email="johndoe@example.com")
        prov_element = user.to_prov_element()
        assert prov_element.identifier == "User?name=John Doe&email=johndoe@example.com"
        assert prov_element.attributes == [
            ("name", "John Doe"),
            ("email", "johndoe@example.com"),
            ("prov_role", None),
            ("prov_type", ProvType.USER),
        ]

        # Test to_prov_element() method with all attributes
        user = User(
            name="Jane Smith",
            email="janesmith@example.com",
            gitlab_username="janesmith",
            github_username="janesmith",
            gitlab_id="123",
            github_id="456",
            prov_role="developer",
        )
        prov_element = user.to_prov_element()
        assert prov_element.identifier == "User?name=Jane Smith&email=janesmith@example.com"
        assert prov_element.attributes == [
            ("name", "Jane Smith"),
            ("email", "janesmith@example.com"),
            ("gitlab_username", "janesmith"),
            ("github_username", "janesmith"),
            ("gitlab_id", "123"),
            ("github_id", "456"),
            ("prov_role", "developer"),
            ("prov_type", ProvType.USER),
        ]
