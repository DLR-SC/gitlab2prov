import random
import re
import string

from gitlab2prov.adapters.fetch.annotations.classifiers import Classifier
from gitlab2prov.adapters.fetch.annotations.classifiers import ImportStatement
from gitlab2prov.adapters.fetch.annotations.classifiers import match_len


class TestMatchLength:
    def test_no_match_has_no_length(self):
        match = re.search("\d", "a")
        assert match_len(match) is None

    def test_n_match_length(self):
        for idx in range(1, 1000):
            pattern = "\d{%d}" % idx
            s = "".join(random.choices(string.digits, k=idx))
            match = re.search(pattern, s)
            assert match_len(match) == idx


class TestClassifier:
    def test_longest_matching_classifier_wins_selection(self):
        classifiers = [
            Classifier(regexes=["\d"]),
            Classifier(regexes=["\d{2}"]),
            Classifier(regexes=["\d{3}"]),
        ]
        for classifier in classifiers:
            classifier.matches(string.digits)
        assert max(classifiers, key=len) == classifiers[-1]

    def test_matches_should_return_true_if_any_pattern_matches(self):
        classifier = Classifier(regexes=[r"\d", r"\s"])
        assert classifier.matches(string.digits) == True

    def test_matches_should_return_false_if_no_pattern_matches(self):
        c = Classifier(regexes=[r"\d", r"\s"])
        assert c.matches(string.ascii_letters) == False

    def test_matches_should_store_the_longest_match_in_the_class_attributes(self):
        regexes = [r"\d{1}", r"\d{2}", r"\d{3}"]
        classifier = Classifier(regexes=regexes)
        classifier.matches(string.digits)
        assert classifier.match.re.pattern == regexes[-1]


class TestImportStatement:
    def test_import_statement_removes_nothing_if_no_match_was_found(self):
        imp = ImportStatement(regexes=[r"\d{3}"])
        imp.matches(string.ascii_letters)
        assert imp.replace(string.ascii_letters) == string.ascii_letters

    def test_import_statement_removes_only_the_leftmost_occurence(self):
        imp = ImportStatement(regexes=[r"\d{3}"])
        imp.matches(string.digits)
        assert imp.replace(string.digits) == string.digits[3:]
