import random
import re
import string

import pytest

from gitlab2prov.adapters.fetch.annotations.classifiers import Classifier
from gitlab2prov.adapters.fetch.annotations.classifiers import ImportStatement
from gitlab2prov.adapters.fetch.annotations.classifiers import match_length


class TestMatchLength:
    def test_raises_value(self):
        with pytest.raises(TypeError):
            match_length(None)

    def test_match_length_with_n_length_matches(self):
        for idx in range(1, 1000):
            pattern = "\d{%d}" % idx
            s = "".join(random.choices(string.digits, k=idx))
            match = re.search(pattern, s)
            assert match_length(match) == idx


class TestClassifier:
    def test_longest_matching_classifier_wins_selection(self):
        classifiers = [
            Classifier(patterns=["\d{1}"]),
            Classifier(patterns=["\d{2}"]),
            Classifier(patterns=["\d{3}"]),
        ]
        for classifier in classifiers:
            classifier.matches(string.digits)
        assert max(classifiers, key=len) == classifiers[-1]

    def test_matches_should_return_true_if_any_pattern_matches(self):
        classifier = Classifier(patterns=[r"\d", r"\s"])
        assert classifier.matches(string.digits) == True

    def test_matches_should_return_false_if_no_pattern_matches(self):
        c = Classifier(patterns=[r"\d", r"\s"])
        assert c.matches(string.ascii_letters) == False

    def test_matches_should_store_the_longest_match_in_the_class_attributes(self):
        regexes = [r"\d{1}", r"\d{2}", r"\d{3}"]
        classifier = Classifier(patterns=regexes)
        classifier.matches(string.digits)
        assert classifier.match.re.pattern == regexes[-1]

    def test_groupdict_should_return_empty_dict_if_no_pattern_matches(self):
        classifier = Classifier(patterns=[r"\d"])
        classifier.matches(string.ascii_letters)
        assert classifier.groupdict() == dict()

    def test_groupdict_should_return_captured_groups_if_a_pattern_matches(self):
        classifier = Classifier(patterns=[r"(?P<number>\d)"])
        classifier.matches(string.digits)
        assert classifier.groupdict() == {"number": string.digits[0]}

    def test_length_should_be_0_if_no_match_was_found(self):
        classifier = Classifier(patterns=[r"\d"])
        classifier.matches(string.ascii_letters)
        assert len(classifier) == 0

    def test_length_should_be_the_span_of_the_found_match(self):
        classifier = Classifier(patterns=[r"\d"])
        classifier.matches(string.digits)
        assert len(classifier) == 1


class TestImportStatement:
    def test_replace_returns_unchanged_string_if_no_match_was_found(self):
        imp = ImportStatement(patterns=[r"\d{3}"])
        imp.matches(string.ascii_letters)
        assert imp.replace(string.ascii_letters) == string.ascii_letters

    def test_import_statement_removes_only_the_leftmost_occurence(self):
        imp = ImportStatement(patterns=[r"\d{3}"])
        imp.matches(string.digits)
        assert imp.replace(string.digits) == string.digits[3:]

    def test_removes_trailing_whitespace_after_import_pattern_replacement(self):
        imp = ImportStatement(patterns=[r"\d{3}"])
        s = f"{string.whitespace}{string.digits}{string.whitespace}"
        imp.matches(s)
        assert not imp.replace(s).endswith(" ")
        assert not imp.replace(s).startswith(" ")
