from gitlab2prov.adapters.fetch.annotations import CLASSIFIERS
from gitlab2prov.adapters.fetch.annotations.parse import classify_system_note
from gitlab2prov.adapters.fetch.annotations.parse import longest_matching_classifier
from gitlab2prov.adapters.fetch.annotations.parse import normalize


class TestNormalize:
    def test_removes_trailing_whitespace(self):
        string = "  test  "
        assert not normalize(string).startswith(" ")
        assert not normalize(string).endswith(" ")

    def test_lowercase(self):
        string = "TEST"
        assert normalize(string).islower()


class TestLongestMatchingClassifier:
    def test_returns_classifier_with_the_longest_match(self):
        string = "changed epic to slug&123"
        assert longest_matching_classifier(string) is CLASSIFIERS[1]
        assert longest_matching_classifier(string).name == "change_epic"
        string = "close via merge request slug!123"
        assert longest_matching_classifier(string) is CLASSIFIERS[7]
        assert longest_matching_classifier(string).name == "close_by_external_merge_request"
        string = "enabled automatic add to merge train when the pipeline for 12345abcde succeeds"
        assert longest_matching_classifier(string) is CLASSIFIERS[-1]
        assert longest_matching_classifier(string).name == "enable_automatic_add_to_merge_train"

    def test_returns_none_if_no_match_was_found(self):
        string = "NOT_MATCHABLE"
        assert longest_matching_classifier(string) is None


class TestClassifySystemNote:
    def test_returns_import_statement_capture_groups(self):
        expected_captures = {"pre_import_author": "original-author"}
        string = "*by original-author on 1970-01-01T00:00:00 (imported from gitlab project)*"
        assert classify_system_note(string)[1] == expected_captures
        string = "*by original-author on 1970-01-01 00:00:00 UTC (imported from gitlab project)*"
        assert classify_system_note(string)[1] == expected_captures

    def test_returns_annotation_classifier_capture_groups(self):
        string = "assigned to @developer"
        expected_captures = {"user_name": "developer"}
        assert classify_system_note(string)[1] == expected_captures

    def test_returns_combined_capture_groups_of_the_import_statement_and_the_classifier(
        self,
    ):
        string = "assigned to @developer *by original-author on 1970-01-01T00:00:00 (imported from gitlab project)*"
        expected_captures = {
            "user_name": "developer",
            "pre_import_author": "original-author",
        }
        assert classify_system_note(string)[1] == expected_captures

    def test_returns_classifier_name_for_known_string(self):
        string = "assigned to @developer"
        expected_name = "assign_user"
        assert classify_system_note(string)[0] == expected_name

    def test_returns_default_annotation_for_unknown_string(self):
        string = "UNKNOWN"
        expected_name = "default_annotation"
        assert classify_system_note(string)[0] == expected_name
