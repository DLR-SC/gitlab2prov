from gitlab2prov import config

from tests.random_refs import random_suffix


class TestDecodeCsvStr:
    def test_a_single_url(self):
        url = f"project-url-{random_suffix()}"
        expected_list = [url]
        assert config.parse_csv_str(url) == expected_list
    
    def test_multiple_urls(self):
        url1 = f"project-url-{random_suffix()}"
        url2 = f"project-url-{random_suffix()}"
        urls = ",".join([url1, url2])
        expected_list = [url1, url2]
        assert config.parse_csv_str(urls) == expected_list
        
    def test_multiple_urls_with_varying_quotation(self):
        url1 = f"'project-url-{random_suffix()}'"
        url2 = f"'project-url-{random_suffix()}'"
        urls = ",".join([url1, url2])
        expected_list = [url1.replace("'", ""), url2.replace("'", "")]
        assert config.parse_csv_str(urls) == expected_list
        
        url1 = f'"project-url-{random_suffix()}"'
        url2 = f'"project-url-{random_suffix()}"'
        urls = ",".join([url1, url2])
        expected_list = [url1.replace('"', ""), url2.replace('"', "")]
        assert config.parse_csv_str(urls) == expected_list
