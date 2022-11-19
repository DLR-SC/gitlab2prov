from gitlab2prov.adapters.fetch import utils


class TestHelpers:
    def test_project_slug(self):
        expected_slug = "owner/project"
        assert expected_slug == utils.project_slug("https://gitlab.com/owner/project")

    def test_gitlab_url(self):
        expected_url = "https://gitlab.com"
        assert expected_url == utils.instance_url("https://gitlab.com/owner/project")
        
    def test_github_url(self):
        expected_url = "https://github.com"
        assert expected_url == utils.instance_url("https://github.com/owner/project")

    def test_clone_over_https_url(self):
        expected_gitlab_url = "https://gitlab.com:TOKEN@gitlab.com/owner/project"
        assert expected_gitlab_url == utils.clone_over_https_url(
            "https://gitlab.com/owner/project", "TOKEN", "gitlab"
        )
        expected_github_url = "https://TOKEN@github.com/owner/project.git"
        assert expected_github_url == utils.clone_over_https_url(
            "https://github.com/owner/project", "TOKEN", "github"
        )
