import uuid
import logging
from typing import Sequence, Pattern, Union

import regex
import gitlab.v4.objects as v4

from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvRole


log = logging.getLogger(__name__)


Note = Union[v4.ProjectIssueNote, v4.ProjectMergeRequestNote]
Comment = v4.ProjectCommitComment
Label = Union[
    v4.ProjectIssueResourceLabelEvent,
    v4.ProjectMergeRequestResourceLabelEvent,
]
AwardEmoji = Union[
    v4.ProjectIssueAwardEmoji,
    v4.ProjectIssueNoteAwardEmoji,
    v4.ProjectMergeRequestAwardEmoji,
    v4.ProjectMergeRequestNoteAwardEmoji,
]
Parseable = Union[Note, Label, AwardEmoji, Comment]


def re_compile(*regular_expressions: str):
    # combine multiple regular expressions into one by 'or'-ing
    ored = "|".join(regular_expressions)
    # wrap in branch reset expression (?|...|...)
    # to be able to reuse the same capture group names
    # across alternative branches
    branch_reset = f"(?|{ored})"
    # compile the pattern and return it
    # the regex pkg pattern is compatible with pythons re implementation
    return regex.compile(branch_reset)


classifiers: dict[str, Pattern] = {
    "change_target_branch": re_compile(
        r"^changed target branch from `(?P<old_target_branch>.+)` to `(?P<new_target_branch>.+)`$"
    ),
    "change_epic": re_compile(
        r"^changed epic to &(?P<epic_iid>\d+)$",
        r"^changed epic to &(?P<epic_name>.+)$",
        r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>\d+)$",
        r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>.+)$",
    ),
    "remove_from_external_epic": re_compile(
        r"^removed from epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
        r"^removed from epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
    ),
    "add_to_external_epic": re_compile(
        r"^added to epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
        r"^added to epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
    ),
    "remove_from_epic": re_compile(
        r"^removed from epic &(?P<epic_iid>\d+)$",
        r"^removed from epic &(?P<epic_name>.+)$",
    ),
    "add_to_epic": re_compile(
        r"^added to epic &(?P<epic_iid>\d+)$",
        r"^added to epic &(?P<epic_name>.+)$",
    ),
    "close_by_external_commit": re_compile(
        r"^closed via commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]+)$"
    ),
    "close_by_external_merge_request": re_compile(
        r"^close via merge request (?P<project_slug>.+?)!(?P<merge_request_iid>\d+)$"
    ),
    "close_by_merge_request": re_compile(
        r"^closed via merge request !(?P<merge_request_iid>.+)$",
        r"^status changed to closed by merge request !(?P<merge_request_iid>.+)$",
    ),
    "close_by_commit": re_compile(
        r"^closed via commit (?P<commit_sha>[a-z0-9]+)$",
        r"^status changed to closed by commit (?P<commit_sha>[a-z0-9]+)$",
    ),
    "restore_source_branch": re_compile(
        r"^restored source branch `(?P<branch_name>.+)`$",
    ),
    "remove_label": re_compile(r"^removed ~(?P<label_id>\d+) label$"),
    "add_label": re_compile(r"^added ~(?P<label_id>\d+) label$"),
    "create_branch": re_compile(
        r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\).*$"
    ),
    "mark_task_as_incomplete": re_compile(
        r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as incomplete$"
    ),
    "mark_task_as_done": re_compile(
        r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as completed$",
    ),
    "add_commits": re_compile(
        r"added (?P<number_of_commits>\d+)\scommit[s]?\n\n.+(?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)<.*",
        r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)\n)+$",
        r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{11}) - (?P<title>.+?)\n)+$",
        r"^added (?P<number_of_commits>\d+) commit[s]?(?:.*\n?)*$",
        r"^added 0 new commits:\n\n$",  # seems weird
    ),
    "address_in_merge_request": re_compile(
        r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"
    ),
    "unmark_as_work_in_progress": re_compile(
        r"^unmarked as a [*]{2}work in progress[*]{2}$",
        r"^unmarked this merge request as a work in progress$",
    ),
    "mark_as_work_in_progress": re_compile(
        r"^marked as a [*]{2}work in progress[*]{2}$",
        r"^marked this merge request as a [*]{2}work in progress[*]{2}$",
    ),
    "merge": re_compile(
        r"^merged$",
        r"^status changed to merged$",
    ),
    "change_description": re_compile(r"^changed the description$"),
    "change_title": re_compile(
        r"^changed title from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
        r"^changed title: [*]{2}(?P<old_title>.+)[*]{2} → [*]{2}(?P<new_title>.+)[*]{2}$",
        r"^title changed from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
    ),
    "move_from": re_compile(r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"),
    "move_to": re_compile(r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"),
    "reopen": re_compile(r"^reopened$", r"^status changed to reopened$"),
    "close": re_compile(
        r"^closed$",
        r"^status changed to closed$",
    ),
    "unrelate_from_external_issue": re_compile(
        r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
    ),
    "relate_to_external_issue": re_compile(
        r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
    ),
    "unrelate_from_issue": re_compile(
        r"^removed the relation with #(?P<issue_iid>\d+)$"
    ),
    "relate_to_issue": re_compile(
        r"^marked this issue as related to #(?P<issue_iid>\d+)$"
    ),
    "has_duplicate": re_compile(
        r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"
    ),
    "mark_as_duplicate": re_compile(
        r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"
    ),
    "make_visible": re_compile(
        r"^made the issue visible to everyone$",
        r"^made the issue visible$",
    ),
    "make_confidential": re_compile(r"^made the issue confidential$"),
    "remove_weight": re_compile(r"^removed the weight$"),
    "change_weight": re_compile(r"^changed weight to [*]{2}(?P<weight>\d+)[*]{2}$"),
    "remove_due_date": re_compile(r"^removed due date$"),
    "change_due_date": re_compile(
        r"^changed due date to (?P<month>(?:january|february|march|april|may|june|july|august|september|october|november|december)) (?P<day>\d\d), (?P<year>\d{4})$"
    ),
    "remove_time_estimate": re_compile(r"^removed time estimate$"),
    "change_time_estimate": re_compile(
        r"^changed time estimate to"
        + r"(?:\s(?P<months>[-]?\d+)mo)?"
        + r"(?:\s(?P<weeks>[-]?\d+)w)?"
        + r"(?:\s(?P<days>[-]?\d+)d)?"
        + r"(?:\s(?P<hours>[-]?\d+)h)?"
        + r"(?:\s(?P<minutes>[-]?\d+)m)?"
        + r"(?:\s(?P<seconds>[-]?\d+)s)?$"
    ),
    "unlock_merge_request": re_compile(r"^unlocked this merge request$"),
    "lock_merge_request": re_compile(r"^locked this merge request$"),
    "unlock_issue": re_compile(r"^unlocked this issue$"),
    "lock_issue": re_compile(r"^locked this issue$"),
    "remove_spend_time": re_compile(r"^removed time spent$"),
    "subtract_spend_time": re_compile(
        r"^subtracted"
        + r"(?:\s(?P<months>\d+)mo)?"
        + r"(?:\s(?P<weeks>\d+)w)?"
        + r"(?:\s(?P<days>\d+)d)?"
        + r"(?:\s(?P<hours>\d+)h)?"
        + r"(?:\s(?P<minutes>\d+)m)?"
        + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
    ),
    "add_spend_time": re_compile(
        r"^added"
        + r"(?:\s(?P<months>\d+)mo)?"
        + r"(?:\s(?P<weeks>\d+)w)?"
        + r"(?:\s(?P<days>\d+)d)?"
        + r"(?:\s(?P<hours>\d+)h)?"
        + r"(?:\s(?P<minutes>\d+)m)?"
        + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
    ),
    "remove_milestone": re_compile(r"^removed milestone$", r"^milestone removed$"),
    "change_milestone": re_compile(
        r"^changed milestone to %(?P<milestone_iid>\d+)$",
        r"^changed milestone to %(?P<milestone_name>.+)$",
        r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_iid>\d+)$",
        r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_name>.+)$",
        r"^milestone changed to %(?P<milestone_iid>\d+)$",
        r"^milestone changed to \[(?P<release_name>.+)\]\((?P<release_link>.+)\)$",
        r"^milestone changed to (?P<release_name>.+)$",
    ),
    "unassign_user": re_compile(
        r"^unassigned @(?P<user_name>.*)$",
        r"^removed assignee$",
    ),
    "assign_user": re_compile(r"^assigned to @(?P<user_name>.*)$"),
    "mention_in_external_merge_request": re_compile(
        r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"
    ),
    "mention_in_merge_request": re_compile(
        r"^mentioned in merge request !(?P<merge_request_iid>\d+)$",
    ),
    "mention_in_external_commit": re_compile(
        r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$",
    ),
    "mention_in_commit": re_compile(
        r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$",
    ),
    "mention_in_external_issue": re_compile(
        r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$",
    ),
    "mention_in_issue": re_compile(
        r"^mentioned in issue #(?P<issue_iid>\d+)$",
    ),
    "resolve_threads": re_compile(r"^resolved all threads$"),
    "approve_merge_request": re_compile(r"^approved this merge request$"),
    "resolve_all_discussions": re_compile(
        r"^resolved all discussions$",
    ),
    "unapprove_merge_request": re_compile(r"^unapproved this merge request$"),
    "automatic_merge_on_pipeline_completion_enabled": re_compile(
        r"^enabled an automatic merge when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
    ),
    "automatic_merge_on_build_success_enabled": re_compile(
        r"^enabled an automatic merge when the build for (?P<commit_sha>[0-9a-z]+) succeeds$",
    ),
    "abort_automatic_merge": re_compile(
        r"^aborted the automatic merge because (?P<abort_reason>[a-z\s]+)$"
    ),
    "cancel_automatic_merge": re_compile(
        r"^canceled the automatic merge$",
    ),
    "create_issue_from_discussion": re_compile(
        r"^created #(?P<issue_iid>\d+) to continue this discussion$"
    ),
    "marked_merge_request_ready": re_compile(
        r"^marked this merge request as \*\*ready\*\*$"
    ),
    "marked_merge_request_note": re_compile(
        r"^marked this merge request as \*\*draft\*\*$"
    ),
    "requested_review": re_compile(
        r"^requested review from @(?P<user_name>.*)$",
        r"^requested review from @(?P<user_name>.*) and @(?P<user_name2>.*)$",
    ),
    "cancel_review_request": re_compile(
        r"^removed review request for @(?P<user_name>.*)$"
    ),
    "mention_in_epic": re_compile(r"^mentioned in epic &(?P<noteable_iid>\d+)$"),
    "reassigned": re_compile(
        r"^reassigned to @(?P<user_name>.*)$",
    ),
    "merge_request_removed": re_compile(
        r"^removed this merge request from the merge train because no stages / jobs for this pipeline.$"
    ),
    "merge_train_started": re_compile(
        r"^started a merge train$",
    ),
    "automatic_add_to_merge_train_enabled": re_compile(
        r"^enabled automatic add to merge train when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
    ),
}


import_pattern: Pattern = re_compile(
    r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \(imported from gitlab project\)\*",
    r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC \(imported from gitlab project\)\*",
)


def classify_by_longest_match(s: str, patterns: dict[str, Pattern]):
    matches, captured = {}, {}
    for cls, pattern in patterns.items():
        lowered = s.lower().strip()
        imported = import_pattern.search(lowered)
        if imported:
            captured.update(imported.groupdict())
        wo_import = import_pattern.sub("", lowered)
        match = pattern.search(wo_import)
        if match:
            matches[cls] = match
    max_match = max(matches, key=matches.get, default="default_annotation")
    if max_match == "default_annotation":
        log.debug(f"No matching classifier found for note with body={s}")
        return max_match, captured
    captured.update(matches[max_match].groupdict())
    return max_match, captured


def parse_system_note(note: Note):
    annotator = objects.User(
        note.author.get("name"),
        note.author.get("email"),
        note.author.get("username"),
        note.author.get("id"),
        ProvRole.Annotator,
    )
    annotation_type, kwargs = classify_by_longest_match(note.body, classifiers)
    return objects.Annotation(
        note.id,
        annotation_type,
        note.body,
        annotator,
        note.created_at,
        note.created_at,
        kwargs,
    )


def parse_commit_comment(comment: Comment):
    annotator = objects.User(
        comment.author.get("name"),
        comment.author.get("email"),
        comment.author.get("username"),
        comment.author.get("id"),
        ProvRole.Annotator,
    )
    return objects.Annotation(
        f"{uuid.uuid4()}{annotator.gitlab_id}{abs(hash(comment.note))}",
        "add_comment",
        comment.note,
        annotator,
        comment.created_at,
        comment.created_at,
    )


def parse_note(note: Note):
    annotator = objects.User(
        note.author.get("name"),
        note.author.get("email"),
        note.author.get("username"),
        note.author.get("id"),
        ProvRole.Annotator,
    )
    return objects.Annotation(
        note.id,
        "add_note",
        note.body,
        annotator,
        note.created_at,
        note.created_at,
    )


def parse_award(award: AwardEmoji):
    annotator = objects.User(
        award.user.get("name"),
        award.user.get("email"),
        award.user.get("username"),
        award.user.get("id"),
        ProvRole.Annotator,
    )
    return objects.Annotation(
        award.id,
        "award_emoji",
        award.name,
        annotator,
        award.created_at,
        award.created_at,
    )


def parse_label(label: Label):
    annotator = objects.User(
        label.user.get("name"),
        label.user.get("email"),
        label.user.get("username"),
        label.user.get("id"),
        ProvRole.Annotator,
    )
    return objects.Annotation(
        label.id,
        f"{label.action}_label",
        label.action,
        annotator,
        label.created_at,
        label.created_at,
    )


def parse_annotation(parseable: Parseable):
    if isinstance(parseable, Note):
        if hasattr(parseable, "system") and parseable.system:
            return parse_system_note(parseable)
        else:
            return parse_note(parseable)
    if isinstance(parseable, Comment):
        return parse_commit_comment(parseable)
    elif isinstance(parseable, Label):
        return parse_label(parseable)
    elif isinstance(parseable, AwardEmoji):
        return parse_award(parseable)
    else:
        print(type(parseable))
        return


def parse_annotations(parseables: Sequence[Parseable]):
    annotations = (parse_annotation(parseable) for parseable in parseables)
    return list(sorted(annotations, key=lambda annotation: annotation.prov_start))