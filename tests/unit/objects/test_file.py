from gitlab2prov.domain.objects import File


class TestFile:
    def test_file_creation(self):
        # Test File object creation
        file_obj = File(name="test_file.txt", path="/path/to/file", commit="12345")
        assert file_obj.name == "test_file.txt"
        assert file_obj.path == "/path/to/file"
        assert file_obj.commit == "12345"

    def test_identifier_property(self):
        # Test identifier property
        file_obj = File(name="test_file.txt", path="/path/to/file", commit="12345")
        assert (
            file_obj.identifier.localpart
            == "File?name=test_file.txt&path=/path/to/file&commit=12345"
        )

    def test_to_prov_element_method(self):
        # Test to_prov_element() method
        file_obj = File(name="test_file.txt", path="/path/to/file", commit="12345")
        prov_entity = file_obj.to_prov_element()
        assert prov_entity.get_attribute("name") == "test_file.txt"
        assert prov_entity.get_attribute("path") == "/path/to/file"
        assert prov_entity.get_attribute("commit") == "12345"
