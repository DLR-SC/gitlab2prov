import re
from typing import Any
from dataclasses import dataclass
from dataclasses import field
from dataclasses import InitVar

import logging


log = logging.getLogger(__name__)


@dataclass(kw_only=True, order=True)
class Classifier:
    name: str = field(compare=False)

    regexps: InitVar[list[str]] = field(compare=False)
    compiled: list[re.Pattern] = field(compare=False, init=False)

    match: re.Match | None = field(compare=True, default=None)

    def __post_init__(self, regexps):
        self.compiled = [re.compile(p) for p in regexps]

    def matches(self, string: str) -> bool:
        matches = []
        for pattern in self.compiled:
            if match := re.search(pattern, string):
                matches.append(match)
        self.match = max(matches, default=None)
        return self.match is not None

    def groupdict(self) -> dict[str, Any] | None:
        if self.match:
            return self.match.groupdict()


@dataclass
class ImportStatement(Classifier):
    name: None = None

    def replace(self, string: str):
        log.debug(f"IMPORT Statement removed! {string=}")
        return self.match.re.sub(string=string, repl="")


CLASSIFIERS = [
    Classifier(
        name="change_target_branch",
        regexps=[
            r"^changed target branch from `(?P<old_target_branch>.+)` to `(?P<new_target_branch>.+)`$"
        ],
    ),
    Classifier(
        name="change_epic",
        regexps=[
            r"^changed epic to &(?P<epic_iid>\d+)$",
            r"^changed epic to &(?P<epic_name>.+)$",
            r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>\d+)$",
            r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    Classifier(
        name="add_to_epic",
        regexps=[
            r"^added to epic &(?P<epic_iid>\d+)$",
            r"^added to epic &(?P<epic_name>.+)$",
        ],
    ),
    Classifier(
        name="remove_from_epic",
        regexps=[
            r"^removed from epic &(?P<epic_iid>\d+)$",
            r"^removed from epic &(?P<epic_name>.+)$",
        ],
    ),
    Classifier(
        name="add_to_external_epic",
        regexps=[
            r"^added to epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
            r"^added to epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    Classifier(
        name="remove_from_external_epic",
        regexps=[
            r"^removed from epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
            r"^removed from epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
        ],
    ),
    Classifier(
        name="close_by_external_commit",
        regexps=[r"^closed via commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]+)$"],
    ),
    Classifier(
        name="close_by_external_merge_request",
        regexps=[
            r"^close via merge request (?P<project_slug>.+?)!(?P<merge_request_iid>\d+)$"
        ],
    ),
    Classifier(
        name="close_by_merge_request",
        regexps=[
            r"^closed via merge request !(?P<merge_request_iid>.+)$",
            r"^status changed to closed by merge request !(?P<merge_request_iid>.+)$",
        ],
    ),
    Classifier(
        name="close_by_commit",
        regexps=[
            r"^closed via commit (?P<commit_sha>[a-z0-9]+)$",
            r"^status changed to closed by commit (?P<commit_sha>[a-z0-9]+)$",
        ],
    ),
    Classifier(
        name="restore_source_branch",
        regexps=[
            r"^restored source branch `(?P<branch_name>.+)`$",
        ],
    ),
    Classifier(name="remove_label", regexps=[r"^removed ~(?P<label_id>\d+) label$"]),
    Classifier(name="add_label", regexps=[r"^added ~(?P<label_id>\d+) label$"]),
    Classifier(
        name="create_branch",
        regexps=[
            r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\).*$"
        ],
    ),
    Classifier(
        name="mark_task_as_incomplete",
        regexps=[
            r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as incomplete$"
        ],
    ),
    Classifier(
        name="mark_task_as_done",
        regexps=[
            r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as completed$",
        ],
    ),
    Classifier(
        name="add_commits",
        regexps=[
            r"added (?P<number_of_commits>\d+)\scommit[s]?\n\n.+(?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)<.*",
            r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)\n)+$",
            r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{11}) - (?P<title>.+?)\n)+$",
            r"^added (?P<number_of_commits>\d+) commit[s]?(?:.*\n?)*$",
            r"^added 0 new commits:\n\n$",  # seems weird
        ],
    ),
    Classifier(
        name="address_in_merge_request",
        regexps=[
            r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"
        ],
    ),
    Classifier(
        name="unmark_as_work_in_progress",
        regexps=[
            r"^unmarked as a [*]{2}work in progress[*]{2}$",
            r"^unmarked this merge request as a work in progress$",
        ],
    ),
    Classifier(
        name="mark_as_work_in_progress",
        regexps=[
            r"^marked as a [*]{2}work in progress[*]{2}$",
            r"^marked this merge request as a [*]{2}work in progress[*]{2}$",
        ],
    ),
    Classifier(
        name="status_changed_to_merged",
        regexps=[
            r"^merged$",
            r"^status changed to merged$",
        ],
    ),
    Classifier(name="change_description", regexps=[r"^changed the description$"]),
    Classifier(
        name="change_title",
        regexps=[
            r"^changed title from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
            r"^changed title: [*]{2}(?P<old_title>.+)[*]{2} → [*]{2}(?P<new_title>.+)[*]{2}$",
            r"^title changed from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
        ],
    ),
    Classifier(
        name="move_from",
        regexps=[r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"],
    ),
    Classifier(
        name="move_to",
        regexps=[r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"],
    ),
    Classifier(name="reopen", regexps=[r"^reopened$", r"^status changed to reopened$"]),
    Classifier(
        name="close",
        regexps=[
            r"^closed$",
            r"^status changed to closed$",
        ],
    ),
    Classifier(
        name="unrelate_from_external_issue",
        regexps=[
            r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
        ],
    ),
    Classifier(
        name="relate_to_external_issue",
        regexps=[
            r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
        ],
    ),
    Classifier(
        name="unrelate_from_issue",
        regexps=[r"^removed the relation with #(?P<issue_iid>\d+)$"],
    ),
    Classifier(
        name="relate_to_issue",
        regexps=[r"^marked this issue as related to #(?P<issue_iid>\d+)$"],
    ),
    Classifier(
        name="has_duplicate",
        regexps=[r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"],
    ),
    Classifier(
        name="mark_as_duplicate",
        regexps=[r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"],
    ),
    Classifier(
        name="make_visible",
        regexps=[
            r"^made the issue visible to everyone$",
            r"^made the issue visible$",
        ],
    ),
    Classifier(name="make_confidential", regexps=[r"^made the issue confidential$"]),
    Classifier(name="remove_weight", regexps=[r"^removed the weight$"]),
    Classifier(
        name="change_weight",
        regexps=[r"^changed weight to [*]{2}(?P<weight>\d+)[*]{2}$"],
    ),
    Classifier(name="remove_due_date", regexps=[r"^removed due date$"]),
    Classifier(
        name="change_due_date",
        regexps=[
            r"^changed due date to (?P<month>(?:january|february|march|april|may|june|july|august|september|october|november|december)) (?P<day>\d\d), (?P<year>\d{4})$"
        ],
    ),
    Classifier(name="remove_time_estimate", regexps=[r"^removed time estimate$"]),
    Classifier(
        name="change_time_estimate",
        regexps=[
            r"^changed time estimate to"
            + r"(?:\s(?P<months>[-]?\d+)mo)?"
            + r"(?:\s(?P<weeks>[-]?\d+)w)?"
            + r"(?:\s(?P<days>[-]?\d+)d)?"
            + r"(?:\s(?P<hours>[-]?\d+)h)?"
            + r"(?:\s(?P<minutes>[-]?\d+)m)?"
            + r"(?:\s(?P<seconds>[-]?\d+)s)?$"
        ],
    ),
    Classifier(name="unlock_merge_request", regexps=[r"^unlocked this merge request$"]),
    Classifier(name="lock_merge_request", regexps=[r"^locked this merge request$"]),
    Classifier(name="unlock_issue", regexps=[r"^unlocked this issue$"]),
    Classifier(name="lock_issue", regexps=[r"^locked this issue$"]),
    Classifier(name="remove_spent_time", regexps=[r"^removed time spent$"]),
    Classifier(
        name="subtract_spent_time",
        regexps=[
            r"^subtracted"
            + r"(?:\s(?P<months>\d+)mo)?"
            + r"(?:\s(?P<weeks>\d+)w)?"
            + r"(?:\s(?P<days>\d+)d)?"
            + r"(?:\s(?P<hours>\d+)h)?"
            + r"(?:\s(?P<minutes>\d+)m)?"
            + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
        ],
    ),
    Classifier(
        name="add_spent_time",
        regexps=[
            r"^added"
            + r"(?:\s(?P<months>\d+)mo)?"
            + r"(?:\s(?P<weeks>\d+)w)?"
            + r"(?:\s(?P<days>\d+)d)?"
            + r"(?:\s(?P<hours>\d+)h)?"
            + r"(?:\s(?P<minutes>\d+)m)?"
            + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
        ],
    ),
    Classifier(
        name="remove_milestone",
        regexps=[r"^removed milestone$", r"^milestone removed$"],
    ),
    Classifier(
        name="change_milestone",
        regexps=[
            r"^changed milestone to %(?P<milestone_iid>\d+)$",
            r"^changed milestone to %(?P<milestone_name>.+)$",
            r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_iid>\d+)$",
            r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_name>.+)$",
            r"^milestone changed to %(?P<milestone_iid>\d+)$",
            r"^milestone changed to \[(?P<release_name>.+)\]\((?P<release_link>.+)\)$",
            r"^milestone changed to (?P<release_name>.+)$",
        ],
    ),
    Classifier(
        name="unassign_user",
        regexps=[
            r"^unassigned @(?P<user_name>.*)$",
            r"^removed assignee$",
        ],
    ),
    Classifier(name="assign_user", regexps=[r"^assigned to @(?P<user_name>.*)$"]),
    Classifier(
        name="mention_in_external_merge_request",
        regexps=[
            r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"
        ],
    ),
    Classifier(
        name="mention_in_merge_request",
        regexps=[
            r"^mentioned in merge request !(?P<merge_request_iid>\d+)$",
        ],
    ),
    Classifier(
        name="mention_in_external_commit",
        regexps=[
            r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$",
        ],
    ),
    Classifier(
        name="mention_in_commit",
        regexps=[
            r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$",
        ],
    ),
    Classifier(
        name="mention_in_external_issue",
        regexps=[
            r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$",
        ],
    ),
    Classifier(
        name="mention_in_issue",
        regexps=[
            r"^mentioned in issue #(?P<issue_iid>\d+)$",
        ],
    ),
    Classifier(name="resolve_threads", regexps=[r"^resolved all threads$"]),
    Classifier(
        name="approve_merge_request", regexps=[r"^approved this merge request$"]
    ),
    Classifier(
        name="resolve_all_discussions",
        regexps=[
            r"^resolved all discussions$",
        ],
    ),
    Classifier(
        name="unapprove_merge_request", regexps=[r"^unapproved this merge request$"]
    ),
    Classifier(
        name="automatic_merge_on_pipeline_completion_enabled",
        regexps=[
            r"^enabled an automatic merge when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
    Classifier(
        name="automatic_merge_on_build_success_enabled",
        regexps=[
            r"^enabled an automatic merge when the build for (?P<commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
    Classifier(
        name="abort_automatic_merge",
        regexps=[r"^aborted the automatic merge because (?P<abort_reason>[a-z\s]+)$"],
    ),
    Classifier(
        name="cancel_automatic_merge",
        regexps=[
            r"^canceled the automatic merge$",
        ],
    ),
    Classifier(
        name="create_issue_from_discussion",
        regexps=[r"^created #(?P<issue_iid>\d+) to continue this discussion$"],
    ),
    Classifier(
        name="marked_merge_request_ready",
        regexps=[r"^marked this merge request as \*\*ready\*\*$"],
    ),
    Classifier(
        name="marked_merge_request_note",
        regexps=[r"^marked this merge request as \*\*draft\*\*$"],
    ),
    Classifier(
        name="requested_review",
        regexps=[
            r"^requested review from @(?P<user_name>.*)$",
            r"^requested review from @(?P<user_name>.*) and @(?P<user_name2>.*)$",
        ],
    ),
    Classifier(
        name="cancel_review_request",
        regexps=[r"^removed review request for @(?P<user_name>.*)$"],
    ),
    Classifier(
        name="mention_in_epic", regexps=[r"^mentioned in epic &(?P<noteable_iid>\d+)$"]
    ),
    Classifier(
        name="reassigned",
        regexps=[
            r"^reassigned to @(?P<user_name>.*)$",
        ],
    ),
    Classifier(
        name="merge_request_removed",
        regexps=[
            r"^removed this merge request from the merge train because no stages / jobs for this pipeline.$"
        ],
    ),
    Classifier(
        name="merge_train_started",
        regexps=[
            r"^started a merge train$",
        ],
    ),
    Classifier(
        name="automatic_add_to_merge_train_enabled",
        regexps=[
            r"^enabled automatic add to merge train when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
        ],
    ),
]

IMPORT_STATEMENT = ImportStatement(
    regexps=[
        r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \(imported from gitlab project\)\*",
        r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC \(imported from gitlab project\)\*",
    ],
)
