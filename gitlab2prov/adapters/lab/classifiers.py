import logging
import re
from dataclasses import dataclass
from dataclasses import field
from dataclasses import InitVar
from typing import Any


log = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Classifier:
    patterns: InitVar[list[str]]
    compiled: list[re.Pattern] = field(init=False, default_factory=list)
    match: re.Match = field(init=False, default=None)

    def __post_init__(self, regexps: list[str]):
        self.compiled = [re.compile(regex, re.IGNORECASE) for regex in regexps]

    @staticmethod
    def match_length(match: re.Match) -> int:
        if match is None:
            raise TypeError(f"Expected argument of type re.Match, got {type(match)}.")
        return match.end() - match.start()

    def matches(self, string: str) -> bool:
        matches = [match for pt in self.compiled if (match := re.search(pt, string))]
        self.match = max(matches, key=self.match_length, default=None)
        return self.match is not None

    def groupdict(self) -> dict[str, Any]:
        if not self.match:
            return dict()
        return self.match.groupdict()

    def __len__(self) -> int:
        if not self.match:
            return 0
        return self.match_length(self.match)


@dataclass(kw_only=True)
class ImportStatement(Classifier):
    def replace(self, string: str) -> str:
        if not self.match:
            return string
        # replace leftmost occurence
        replaced = self.match.re.sub("", string, count=1)
        # remove trailing whitespace
        return replaced.strip()


@dataclass(kw_only=True)
class AnnotationClassifier(Classifier):
    name: str = field(compare=False)


CLASSIFIERS = [
    AnnotationClassifier(
        name="change_target_branch",
        patterns=[
            r"^changed target branch from `(?P<old_target_branch>.+)` to `(?P<new_target_branch>.+)`$"
        ],
    ),
    AnnotationClassifier(
        name="change_epic",
        patterns=[
            r"^changed epic to &(?P<epic_iid>\d+)$",
            r"^changed epic to &(?P<epic_name>.+)$",
            r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>\d+)$",
            r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="add_to_epic",
        patterns=[
            r"^added to epic &(?P<epic_iid>\d+)$",
            r"^added to epic &(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="remove_from_epic",
        patterns=[
            r"^removed from epic &(?P<epic_iid>\d+)$",
            r"^removed from epic &(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="add_to_external_epic",
        patterns=[
            r"^added to epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
            r"^added to epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="remove_from_external_epic",
        patterns=[
            r"^removed from epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
            r"^removed from epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="close_by_external_commit",
        patterns=[r"^closed via commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]+)$"],
    ),
    AnnotationClassifier(
        name="close_by_external_merge_request",
        patterns=[r"^close via merge request (?P<project_slug>.+?)!(?P<merge_request_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="close_by_merge_request",
        patterns=[
            r"^closed via merge request !(?P<merge_request_iid>.+)$",
            r"^status changed to closed by merge request !(?P<merge_request_iid>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="close_by_commit",
        patterns=[
            r"^closed via commit (?P<commit_sha>[a-z0-9]+)$",
            r"^status changed to closed by commit (?P<commit_sha>[a-z0-9]+)$",
        ],
    ),
    AnnotationClassifier(
        name="restore_source_branch",
        patterns=[
            r"^restored source branch `(?P<branch_name>.+)`$",
        ],
    ),
    AnnotationClassifier(name="remove_label", patterns=[r"^removed ~(?P<label_id>\d+) label$"]),
    AnnotationClassifier(name="add_label", patterns=[r"^added ~(?P<label_id>\d+) label$"]),
    AnnotationClassifier(
        name="create_branch",
        patterns=[r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\).*$"],
    ),
    AnnotationClassifier(
        name="mark_task_as_incomplete",
        patterns=[r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as incomplete$"],
    ),
    AnnotationClassifier(
        name="mark_task_as_done",
        patterns=[
            r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as completed$",
        ],
    ),
    AnnotationClassifier(
        name="add_commits",
        patterns=[
            r"added (?P<number_of_commits>\d+)\scommit[s]?\n\n.+(?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)<.*",
            r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)\n)+$",
            r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{11}) - (?P<title>.+?)\n)+$",
            r"^added (?P<number_of_commits>\d+) commit[s]?(?:.*\n?)*$",
            r"^added 0 new commits:\n\n$",  # seems weird
        ],
    ),
    AnnotationClassifier(
        name="address_in_merge_request",
        patterns=[r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"],
    ),
    AnnotationClassifier(
        name="unmark_as_work_in_progress",
        patterns=[
            r"^unmarked as a [*]{2}work in progress[*]{2}$",
            r"^unmarked this merge request as a work in progress$",
        ],
    ),
    AnnotationClassifier(
        name="mark_as_work_in_progress",
        patterns=[
            r"^marked as a [*]{2}work in progress[*]{2}$",
            r"^marked this merge request as a [*]{2}work in progress[*]{2}$",
        ],
    ),
    AnnotationClassifier(
        name="status_changed_to_merged",
        patterns=[
            r"^merged$",
            r"^status changed to merged$",
        ],
    ),
    AnnotationClassifier(name="change_description", patterns=[r"^changed the description$"]),
    AnnotationClassifier(
        name="change_title",
        patterns=[
            r"^changed title from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
            r"^changed title: [*]{2}(?P<old_title>.+)[*]{2} → [*]{2}(?P<new_title>.+)[*]{2}$",
            r"^title changed from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
        ],
    ),
    AnnotationClassifier(
        name="move_from",
        patterns=[r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="move_to",
        patterns=[r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(name="reopen", patterns=[r"^reopened$", r"^status changed to reopened$"]),
    AnnotationClassifier(
        name="close",
        patterns=[
            r"^closed$",
            r"^status changed to closed$",
        ],
    ),
    AnnotationClassifier(
        name="unrelate_from_external_issue",
        patterns=[r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="relate_to_external_issue",
        patterns=[r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="unrelate_from_issue",
        patterns=[r"^removed the relation with #(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="relate_to_issue",
        patterns=[r"^marked this issue as related to #(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="has_duplicate",
        patterns=[r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"],
    ),
    AnnotationClassifier(
        name="mark_as_duplicate",
        patterns=[r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="make_visible",
        patterns=[
            r"^made the issue visible to everyone$",
            r"^made the issue visible$",
        ],
    ),
    AnnotationClassifier(name="make_confidential", patterns=[r"^made the issue confidential$"]),
    AnnotationClassifier(name="remove_weight", patterns=[r"^removed the weight$"]),
    AnnotationClassifier(
        name="change_weight",
        patterns=[r"^changed weight to [*]{2}(?P<weight>\d+)[*]{2}$"],
    ),
    AnnotationClassifier(name="remove_due_date", patterns=[r"^removed due date$"]),
    AnnotationClassifier(
        name="change_due_date",
        patterns=[
            r"^changed due date to (?P<month>(?:january|february|march|april|may|june|july|august|september|october|november|december)) (?P<day>\d\d), (?P<year>\d{4})$"
        ],
    ),
    AnnotationClassifier(name="remove_time_estimate", patterns=[r"^removed time estimate$"]),
    AnnotationClassifier(
        name="change_time_estimate",
        patterns=[
            r"^changed time estimate to"
            + r"(?:\s(?P<months>[-]?\d+)mo)?"
            + r"(?:\s(?P<weeks>[-]?\d+)w)?"
            + r"(?:\s(?P<days>[-]?\d+)d)?"
            + r"(?:\s(?P<hours>[-]?\d+)h)?"
            + r"(?:\s(?P<minutes>[-]?\d+)m)?"
            + r"(?:\s(?P<seconds>[-]?\d+)s)?$"
        ],
    ),
    AnnotationClassifier(name="unlock_merge_request", patterns=[r"^unlocked this merge request$"]),
    AnnotationClassifier(name="lock_merge_request", patterns=[r"^locked this merge request$"]),
    AnnotationClassifier(name="unlock_issue", patterns=[r"^unlocked this issue$"]),
    AnnotationClassifier(name="lock_issue", patterns=[r"^locked this issue$"]),
    AnnotationClassifier(name="remove_spent_time", patterns=[r"^removed time spent$"]),
    AnnotationClassifier(
        name="subtract_spent_time",
        patterns=[
            r"^subtracted"
            + r"(?:\s(?P<months>\d+)mo)?"
            + r"(?:\s(?P<weeks>\d+)w)?"
            + r"(?:\s(?P<days>\d+)d)?"
            + r"(?:\s(?P<hours>\d+)h)?"
            + r"(?:\s(?P<minutes>\d+)m)?"
            + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
        ],
    ),
    AnnotationClassifier(
        name="add_spent_time",
        patterns=[
            r"^added"
            + r"(?:\s(?P<months>\d+)mo)?"
            + r"(?:\s(?P<weeks>\d+)w)?"
            + r"(?:\s(?P<days>\d+)d)?"
            + r"(?:\s(?P<hours>\d+)h)?"
            + r"(?:\s(?P<minutes>\d+)m)?"
            + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
        ],
    ),
    AnnotationClassifier(
        name="remove_milestone",
        patterns=[r"^removed milestone$", r"^milestone removed$"],
    ),
    AnnotationClassifier(
        name="change_milestone",
        patterns=[
            r"^changed milestone to %(?P<milestone_iid>\d+)$",
            r"^changed milestone to %(?P<milestone_name>.+)$",
            r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_iid>\d+)$",
            r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_name>.+)$",
            r"^milestone changed to %(?P<milestone_iid>\d+)$",
            r"^milestone changed to \[(?P<release_name>.+)\]\((?P<release_link>.+)\)$",
            r"^milestone changed to (?P<release_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="unassign_user",
        patterns=[
            r"^unassigned @(?P<user_name>.*)$",
            r"^removed assignee$",
        ],
    ),
    AnnotationClassifier(name="assign_user", patterns=[r"^assigned to @(?P<user_name>.*)$"]),
    AnnotationClassifier(
        name="mention_in_external_merge_request",
        patterns=[r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="mention_in_merge_request",
        patterns=[
            r"^mentioned in merge request !(?P<merge_request_iid>\d+)$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_external_commit",
        patterns=[
            r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_commit",
        patterns=[
            r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_external_issue",
        patterns=[
            r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_issue",
        patterns=[
            r"^mentioned in issue #(?P<issue_iid>\d+)$",
        ],
    ),
    AnnotationClassifier(name="resolve_all_threads", patterns=[r"^resolved all threads$"]),
    AnnotationClassifier(
        name="approve_merge_request", patterns=[r"^approved this merge request$"]
    ),
    AnnotationClassifier(
        name="resolve_all_discussions",
        patterns=[
            r"^resolved all discussions$",
        ],
    ),
    AnnotationClassifier(
        name="unapprove_merge_request", patterns=[r"^unapproved this merge request$"]
    ),
    AnnotationClassifier(
        name="enable_automatic_merge_on_pipeline_completion",
        patterns=[
            r"^enabled an automatic merge when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
    AnnotationClassifier(
        name="enable_automatic_merge_on_build_success",
        patterns=[
            r"^enabled an automatic merge when the build for (?P<commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
    AnnotationClassifier(
        name="abort_automatic_merge",
        patterns=[r"^aborted the automatic merge because (?P<abort_reason>[a-z\s]+)$"],
    ),
    AnnotationClassifier(
        name="cancel_automatic_merge",
        patterns=[
            r"^canceled the automatic merge$",
        ],
    ),
    AnnotationClassifier(
        name="create_issue_from_discussion",
        patterns=[r"^created #(?P<issue_iid>\d+) to continue this discussion$"],
    ),
    AnnotationClassifier(
        name="mark_merge_request_as_ready",
        patterns=[r"^marked this merge request as \*\*ready\*\*$"],
    ),
    AnnotationClassifier(
        name="mark_merge_request_note_as_draft",
        patterns=[r"^marked this merge request as \*\*draft\*\*$"],
    ),
    # TODO: allow n reviewers
    AnnotationClassifier(
        name="request_review",
        patterns=[
            r"^requested review from @(?P<user_name>.*)$",
            r"^requested review from @(?P<user_name>.*) and @(?P<user_name2>.*)$",
        ],
    ),
    # TODO: allow n reviewers
    AnnotationClassifier(
        name="cancel_review_request",
        patterns=[r"^removed review request for @(?P<user_name>.*)$"],
    ),
    AnnotationClassifier(
        name="mention_in_epic", patterns=[r"^mentioned in epic &(?P<noteable_iid>\d+)$"]
    ),
    AnnotationClassifier(
        name="reassign_user",
        patterns=[
            r"^reassigned to @(?P<user_name>.*)$",
        ],
    ),
    AnnotationClassifier(
        name="remove_merge_request_from_merge_train",
        patterns=[
            r"^removed this merge request from the merge train because no stages / jobs for this pipeline.$"
        ],
    ),
    AnnotationClassifier(
        name="start_merge_train",
        patterns=[
            r"^started a merge train$",
        ],
    ),
    AnnotationClassifier(
        name="enable_automatic_add_to_merge_train",
        patterns=[
            r"^enabled automatic add to merge train when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
]

IMPORT_STATEMENT = ImportStatement(
    patterns=[
        r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \(imported from gitlab project\)\*",
        r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC \(imported from gitlab project\)\*",
    ],
)


@dataclass
class SystemNoteClassifier:
    @staticmethod
    def normalize(note: str) -> str:
        return note.strip().lower()

    def longest_matching_classifier(self, note: str) -> AnnotationClassifier:
        matching = (classifier for classifier in CLASSIFIERS if classifier.matches(note))
        return max(matching, key=len, default=None)

    def classify(self, note: str) -> tuple[str, dict[str, str]]:
        # 1. normalize the note
        key_value_pairs = {}
        normalized_note = self.normalize(note)
        # 2. remove import statements, if any and extract the key-value pairs
        if IMPORT_STATEMENT.matches(normalized_note):
            normalized_note = IMPORT_STATEMENT.replace(normalized_note)
            key_value_pairs.update(IMPORT_STATEMENT.groupdict())
        # 3. find the longest matching classifier
        if classifier := self.longest_matching_classifier(normalized_note):
            key_value_pairs.update(classifier.groupdict())
            # 4. return the classifier name and the matched groups
            return classifier.name, key_value_pairs
        # 5. if no classifier matches, return "unknown" and an empty dict
        return "unknown", key_value_pairs
