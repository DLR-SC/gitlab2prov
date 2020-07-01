import pytest
from gitlab2prov.utils.helpers import ptime, by_date, chunks, url_encoded_path, qname
from gitlab2prov.utils.objects import GL2PEvent
from datetime import datetime, timezone, timedelta


control_time = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone(timedelta(hours=1)))


class TestPTime:
    """
    Tests for ptime method of gitlab2prov.utils.helpers.
    """

    def test_valid_value(self):
        """
        Test datetime parsing with valid parameter.
        """
        global control_time
        string = "1970-01-01T00:00:00.00+01:00"
        assert isinstance(ptime(string), datetime)
        assert ptime(string) == control_time

    def test_invalid_value(self):
        """
        Test datetime parsing with invalid parameter.
        """
        string = "invalid"
        with pytest.raises(ValueError):
            ptime(string)

    def test_empty_value(self):
        """
        Test datetime parsing with empty parameter.
        """
        string = ""
        with pytest.raises(ValueError):
            ptime(string)

    def test_invalid_types(self):
        """
        Test datetime parsing with invalid parameter types.
        """
        values = [1.0, 1970, list(), tuple(), dict(), set()]
        for val in values:
            with pytest.raises(TypeError):
                ptime(val)


class TestByDate:
    """
    Tests for by_date method of gitlab2prov.utils.helpers.

    by_date delegates datetime parsing to ptime.
    Therefore parsing tests will remain at ptime.
    """

    def test_valid(self):
        """
        Test by_date with valid parameters.
        """
        global control_time
        value = GL2PEvent(id="id", initiator="", label={}, created_at="1970-01-01T00:00:00.00+01:00")

        assert isinstance(by_date(value), datetime)
        assert by_date(value) == control_time

    def test_invalid_type(self):
        """
        Test by_date with an arg that is not of type gitlab2provEvent.
        """
        values = [19.84, 1970, tuple(), list(), dict(), set()]
        for val in values:
            with pytest.raises(TypeError):
                by_date(val)


class TestChunks:
    """
    Tests for chunks method of gitlab2prov.utils.helpers.
    """

    def test_valid(self):
        """
        Test chunks with valid parameters.
        """
        lst = list(range(1000))
        chunk_size = 10
        chunk_list = list(chunks(lst, chunk_size))

        # expect 100 chunks of len 10
        assert len(chunk_list) == 100
        assert all(len(chunk) == 10 for chunk in chunk_list)

        lst = list(range(100))
        chunk_size = 100
        chunk_list = list(chunks(lst, chunk_size))
        # expect 1 chunk of len 100
        assert len(chunk_list) == 1
        assert all(len(chunk) == 100 for chunk in chunk_list)

    def test_chunk_size_zero(self):
        """
        Test chunks with parameter chunk_size equals zero.
        Should raise ValueError.
        """
        with pytest.raises(ValueError):
            list(chunks(list(range(10)), 0))

    def test_chunk_size_none(self):
        """
        Test chunks with parameter chunk_size equals None.
        Should raise ValueError.
        """
        with pytest.raises(ValueError):
            list(chunks(list(range(10)), None))

    def test_invalid_lst_types(self):
        """
        Test chunks with invalid types of parameter L.
        """
        types = [19.84, 1970, tuple(), dict(), set()]
        for t in types:
            with pytest.raises(TypeError):
                list(chunks(t, 10))

    def test_invalid_chunk_size_types(self):
        """
        Test chunks with invalid type of parameter chunk_size.
        """
        types = [19.84, tuple(), list(), dict(), set(), "string"]
        for t in types:
            with pytest.raises(TypeError):
                list(chunks(list(range(10)), t))


class TestURLEncodedPath:
    """
    Tests for url_encoded_path method of gitlab2prov.utils.helpers.
    """

    def test_valid(self):
        """
        Test url_encoded_path with valid parameters.
        """
        url = "https://example.org/orgname/projectname"
        path = url_encoded_path(url)
        assert isinstance(path, str)
        assert path == "orgname%2Fprojectname"

    def test_trailing_slash(self):
        """
        Test url_encoded_path with url that has a path with a trailing slash.
        """
        url_trailing_slash = "https://example.org/orgname/projectname/"
        path = url_encoded_path(url_trailing_slash)
        assert isinstance(path, str)
        assert path == "orgname%2Fprojectname"

    def test_missing_path(self):
        """
        Test url_encoded_path with url that does not have a parsable path component.
        """
        url_missing_path1 = "https://example.org"
        url_missing_path2 = "https://example.org/"
        with pytest.raises(ValueError):
            url_encoded_path(url_missing_path1)
        with pytest.raises(ValueError):
            url_encoded_path(url_missing_path2)

    def test_invalid_parameter_types(self):
        """
        Test url_encoded_path with invalid parameter types for parameter url.
        """
        types = [1, 1.0, tuple(), list(), dict(), set()]
        for t in types:
            with pytest.raises(TypeError):
                url_encoded_path(t)


class TestQName:
    """
    Tests for qname method of gitlab2prov.utils.helpers.
    """

    def test_valid(self):
        """
        Test qname with valid parameters.
        """
        qn = qname("some-string")
        assert isinstance(qn, str)
        assert qname("s1") == qname("s1")

    def test_invalid_parameter_types(self):
        """
        Test qname with invalid parameter types.
        """
        types = [1, 1.0, tuple(), list(), dict(), set()]
        for t in types:
            with pytest.raises(TypeError):
                qname(t)
