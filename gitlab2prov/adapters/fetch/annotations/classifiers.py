import re
from typing import Any
from dataclasses import dataclass
from dataclasses import field
from dataclasses import InitVar

import logging


log = logging.getLogger(__name__)


def match_len(match: re.Match | None) -> int | None:
    if not match:
        return None
    return match.end() - match.start()


@dataclass(kw_only=True)
class Classifier:
    regexes: InitVar[list[str]]
    patterns: list[re.Pattern] = field(init=False, default_factory=list)
    match: re.Match = field(init=False, default=None)

    def __post_init__(self, regexps: list[str]):
        self.patterns = [re.compile(regex, re.IGNORECASE) for regex in regexps]

    def matches(self, string: str) -> bool:
        matches = [match for pt in self.patterns if (match := re.search(pt, string))]
        self.match = max(matches, key=match_len, default=None)
        return self.match is not None

    def groupdict(self) -> dict[str, Any] | None:
        if not self.match:
            return
        return self.match.groupdict()

    def __len__(self) -> int:
        if not self.match:
            return 0
        return match_len(self.match)


@dataclass(kw_only=True)
class ImportStatement(Classifier):
    def replace(self, string: str) -> str:
        if not self.match:
            return string  # remove only the leftmost matching occurence
        return self.match.re.sub(repl="", string=string, count=1)


@dataclass(kw_only=True)
class AnnotationClassifier(Classifier):
    name: str = field(compare=False)


CLASSIFIERS = [
    AnnotationClassifier(
        name="change_target_branch",
        regexes=[
            r"^changed target branch from `(?P<old_target_branch>.+)` to `(?P<new_target_branch>.+)`$"
        ],
    ),
    AnnotationClassifier(
        name="change_epic",
        regexes=[
            r"^changed epic to &(?P<epic_iid>\d+)$",
            r"^changed epic to &(?P<epic_name>.+)$",
            r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>\d+)$",
            r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="add_to_epic",
        regexes=[
            r"^added to epic &(?P<epic_iid>\d+)$",
            r"^added to epic &(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="remove_from_epic",
        regexes=[
            r"^removed from epic &(?P<epic_iid>\d+)$",
            r"^removed from epic &(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="add_to_external_epic",
        regexes=[
            r"^added to epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
            r"^added to epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="remove_from_external_epic",
        regexes=[
            r"^removed from epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
            r"^removed from epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="close_by_external_commit",
        regexes=[r"^closed via commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]+)$"],
    ),
    AnnotationClassifier(
        name="close_by_external_merge_request",
        regexes=[
            r"^close via merge request (?P<project_slug>.+?)!(?P<merge_request_iid>\d+)$"
        ],
    ),
    AnnotationClassifier(
        name="close_by_merge_request",
        regexes=[
            r"^closed via merge request !(?P<merge_request_iid>.+)$",
            r"^status changed to closed by merge request !(?P<merge_request_iid>.+)$",
        ],
    ),
    AnnotationClassifier(
        name="close_by_commit",
        regexes=[
            r"^closed via commit (?P<commit_sha>[a-z0-9]+)$",
            r"^status changed to closed by commit (?P<commit_sha>[a-z0-9]+)$",
        ],
    ),
    AnnotationClassifier(
        name="restore_source_branch",
        regexes=[
            r"^restored source branch `(?P<branch_name>.+)`$",
        ],
    ),
    AnnotationClassifier(
        name="remove_label", regexes=[r"^removed ~(?P<label_id>\d+) label$"]
    ),
    AnnotationClassifier(
        name="add_label", regexes=[r"^added ~(?P<label_id>\d+) label$"]
    ),
    AnnotationClassifier(
        name="create_branch",
        regexes=[
            r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\).*$"
        ],
    ),
    AnnotationClassifier(
        name="mark_task_as_incomplete",
        regexes=[
            r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as incomplete$"
        ],
    ),
    AnnotationClassifier(
        name="mark_task_as_done",
        regexes=[
            r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as completed$",
        ],
    ),
    AnnotationClassifier(
        name="add_commits",
        regexes=[
            r"added (?P<number_of_commits>\d+)\scommit[s]?\n\n.+(?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)<.*",
            r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)\n)+$",
            r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{11}) - (?P<title>.+?)\n)+$",
            r"^added (?P<number_of_commits>\d+) commit[s]?(?:.*\n?)*$",
            r"^added 0 new commits:\n\n$",  # seems weird
        ],
    ),
    AnnotationClassifier(
        name="address_in_merge_request",
        regexes=[
            r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"
        ],
    ),
    AnnotationClassifier(
        name="unmark_as_work_in_progress",
        regexes=[
            r"^unmarked as a [*]{2}work in progress[*]{2}$",
            r"^unmarked this merge request as a work in progress$",
        ],
    ),
    AnnotationClassifier(
        name="mark_as_work_in_progress",
        regexes=[
            r"^marked as a [*]{2}work in progress[*]{2}$",
            r"^marked this merge request as a [*]{2}work in progress[*]{2}$",
        ],
    ),
    AnnotationClassifier(
        name="status_changed_to_merged",
        regexes=[
            r"^merged$",
            r"^status changed to merged$",
        ],
    ),
    AnnotationClassifier(
        name="change_description", regexes=[r"^changed the description$"]
    ),
    AnnotationClassifier(
        name="change_title",
        regexes=[
            r"^changed title from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
            r"^changed title: [*]{2}(?P<old_title>.+)[*]{2} → [*]{2}(?P<new_title>.+)[*]{2}$",
            r"^title changed from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
        ],
    ),
    AnnotationClassifier(
        name="move_from",
        regexes=[r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="move_to",
        regexes=[r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="reopen", regexes=[r"^reopened$", r"^status changed to reopened$"]
    ),
    AnnotationClassifier(
        name="close",
        regexes=[
            r"^closed$",
            r"^status changed to closed$",
        ],
    ),
    AnnotationClassifier(
        name="unrelate_from_external_issue",
        regexes=[
            r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
        ],
    ),
    AnnotationClassifier(
        name="relate_to_external_issue",
        regexes=[
            r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
        ],
    ),
    AnnotationClassifier(
        name="unrelate_from_issue",
        regexes=[r"^removed the relation with #(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="relate_to_issue",
        regexes=[r"^marked this issue as related to #(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="has_duplicate",
        regexes=[r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"],
    ),
    AnnotationClassifier(
        name="mark_as_duplicate",
        regexes=[r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"],
    ),
    AnnotationClassifier(
        name="make_visible",
        regexes=[
            r"^made the issue visible to everyone$",
            r"^made the issue visible$",
        ],
    ),
    AnnotationClassifier(
        name="make_confidential", regexes=[r"^made the issue confidential$"]
    ),
    AnnotationClassifier(name="remove_weight", regexes=[r"^removed the weight$"]),
    AnnotationClassifier(
        name="change_weight",
        regexes=[r"^changed weight to [*]{2}(?P<weight>\d+)[*]{2}$"],
    ),
    AnnotationClassifier(name="remove_due_date", regexes=[r"^removed due date$"]),
    AnnotationClassifier(
        name="change_due_date",
        regexes=[
            r"^changed due date to (?P<month>(?:january|february|march|april|may|june|july|august|september|october|november|december)) (?P<day>\d\d), (?P<year>\d{4})$"
        ],
    ),
    AnnotationClassifier(
        name="remove_time_estimate", regexes=[r"^removed time estimate$"]
    ),
    AnnotationClassifier(
        name="change_time_estimate",
        regexes=[
            r"^changed time estimate to"
            + r"(?:\s(?P<months>[-]?\d+)mo)?"
            + r"(?:\s(?P<weeks>[-]?\d+)w)?"
            + r"(?:\s(?P<days>[-]?\d+)d)?"
            + r"(?:\s(?P<hours>[-]?\d+)h)?"
            + r"(?:\s(?P<minutes>[-]?\d+)m)?"
            + r"(?:\s(?P<seconds>[-]?\d+)s)?$"
        ],
    ),
    AnnotationClassifier(
        name="unlock_merge_request", regexes=[r"^unlocked this merge request$"]
    ),
    AnnotationClassifier(
        name="lock_merge_request", regexes=[r"^locked this merge request$"]
    ),
    AnnotationClassifier(name="unlock_issue", regexes=[r"^unlocked this issue$"]),
    AnnotationClassifier(name="lock_issue", regexes=[r"^locked this issue$"]),
    AnnotationClassifier(name="remove_spent_time", regexes=[r"^removed time spent$"]),
    AnnotationClassifier(
        name="subtract_spent_time",
        regexes=[
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
        regexes=[
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
        regexes=[r"^removed milestone$", r"^milestone removed$"],
    ),
    AnnotationClassifier(
        name="change_milestone",
        regexes=[
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
        regexes=[
            r"^unassigned @(?P<user_name>.*)$",
            r"^removed assignee$",
        ],
    ),
    AnnotationClassifier(
        name="assign_user", regexes=[r"^assigned to @(?P<user_name>.*)$"]
    ),
    AnnotationClassifier(
        name="mention_in_external_merge_request",
        regexes=[
            r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"
        ],
    ),
    AnnotationClassifier(
        name="mention_in_merge_request",
        regexes=[
            r"^mentioned in merge request !(?P<merge_request_iid>\d+)$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_external_commit",
        regexes=[
            r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_commit",
        regexes=[
            r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_external_issue",
        regexes=[
            r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$",
        ],
    ),
    AnnotationClassifier(
        name="mention_in_issue",
        regexes=[
            r"^mentioned in issue #(?P<issue_iid>\d+)$",
        ],
    ),
    AnnotationClassifier(name="resolve_threads", regexes=[r"^resolved all threads$"]),
    AnnotationClassifier(
        name="approve_merge_request", regexes=[r"^approved this merge request$"]
    ),
    AnnotationClassifier(
        name="resolve_all_discussions",
        regexes=[
            r"^resolved all discussions$",
        ],
    ),
    AnnotationClassifier(
        name="unapprove_merge_request", regexes=[r"^unapproved this merge request$"]
    ),
    AnnotationClassifier(
        name="automatic_merge_on_pipeline_completion_enabled",
        regexes=[
            r"^enabled an automatic merge when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
    AnnotationClassifier(
        name="automatic_merge_on_build_success_enabled",
        regexes=[
            r"^enabled an automatic merge when the build for (?P<commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
    AnnotationClassifier(
        name="abort_automatic_merge",
        regexes=[r"^aborted the automatic merge because (?P<abort_reason>[a-z\s]+)$"],
    ),
    AnnotationClassifier(
        name="cancel_automatic_merge",
        regexes=[
            r"^canceled the automatic merge$",
        ],
    ),
    AnnotationClassifier(
        name="create_issue_from_discussion",
        regexes=[r"^created #(?P<issue_iid>\d+) to continue this discussion$"],
    ),
    AnnotationClassifier(
        name="marked_merge_request_ready",
        regexes=[r"^marked this merge request as \*\*ready\*\*$"],
    ),
    AnnotationClassifier(
        name="marked_merge_request_note",
        regexes=[r"^marked this merge request as \*\*draft\*\*$"],
    ),
    AnnotationClassifier(
        name="requested_review",
        regexes=[
            r"^requested review from @(?P<user_name>.*)$",
            r"^requested review from @(?P<user_name>.*) and @(?P<user_name2>.*)$",
        ],
    ),
    AnnotationClassifier(
        name="cancel_review_request",
        regexes=[r"^removed review request for @(?P<user_name>.*)$"],
    ),
    AnnotationClassifier(
        name="mention_in_epic", regexes=[r"^mentioned in epic &(?P<noteable_iid>\d+)$"]
    ),
    AnnotationClassifier(
        name="reassigned",
        regexes=[
            r"^reassigned to @(?P<user_name>.*)$",
        ],
    ),
    AnnotationClassifier(
        name="merge_request_removed",
        regexes=[
            r"^removed this merge request from the merge train because no stages / jobs for this pipeline.$"
        ],
    ),
    AnnotationClassifier(
        name="merge_train_started",
        regexes=[
            r"^started a merge train$",
        ],
    ),
    AnnotationClassifier(
        name="automatic_add_to_merge_train_enabled",
        regexes=[
            r"^enabled automatic add to merge train when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
]

IMPORT_STATEMENT = ImportStatement(
    regexes=[
        r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \(imported from gitlab project\)\*",
        r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC \(imported from gitlab project\)\*",
    ],
)
