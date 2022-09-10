from gitlab2prov.adapters.fetch import utils


class TestHelpers:
    def test_project_slug(self):
        expected_slug = "group/project"
        assert expected_slug == utils.project_slug("https://gitlab.com/group/project")

    def test_gitlab_url(self):
        expected_url = "https://gitlab.com"
        assert expected_url == utils.gitlab_url("https://gitlab.com/group/project")

    def test_clone_over_https_url(self):
        expected_url = "https://gitlab.com:TOKEN@gitlab.com/group/project"
        assert expected_url == utils.clone_over_https_url(
            "https://gitlab.com/group/project", "TOKEN"
        )
