import uuid
import logging
from typing import Sequence, Pattern, Union

import regex
import gitlab.v4.objects as v4

from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvRole


log = logging.getLogger(__name__)


DEFAULT = "default_annotation"


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


def compile_branch_reset(*regular_expressions: str):
    # combine multiple regular expressions into one by 'or'-ing
    or_expr = "|".join(regular_expressions)
    # wrap in branch reset expression (?|...|...)
    # to be able to reuse the same capture group names
    # across alternative branches
    branch_reset = f"(?|{or_expr})"
    # compile the pattern and return it
    # the regex pkg pattern is compatible with pythons re implementation
    return regex.compile(branch_reset)


CLASSIFIERS: dict[str, Pattern] = {
    "change_target_branch": compile_branch_reset(
        r"^changed target branch from `(?P<old_target_branch>.+)` to `(?P<new_target_branch>.+)`$"
    ),
    "change_epic": compile_branch_reset(
        r"^changed epic to &(?P<epic_iid>\d+)$",
        r"^changed epic to &(?P<epic_name>.+)$",
        r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>\d+)$",
        r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>.+)$",
    ),
    "remove_from_external_epic": compile_branch_reset(
        r"^removed from epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
        r"^removed from epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
    ),
    "add_to_external_epic": compile_branch_reset(
        r"^added to epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
        r"^added to epic (?P<project_slug>.+)&(?P<epic_name>.+)$",
    ),
    "remove_from_epic": compile_branch_reset(
        r"^removed from epic &(?P<epic_iid>\d+)$",
        r"^removed from epic &(?P<epic_name>.+)$",
    ),
    "add_to_epic": compile_branch_reset(
        r"^added to epic &(?P<epic_iid>\d+)$",
        r"^added to epic &(?P<epic_name>.+)$",
    ),
    "close_by_external_commit": compile_branch_reset(
        r"^closed via commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]+)$"
    ),
    "close_by_external_merge_request": compile_branch_reset(
        r"^close via merge request (?P<project_slug>.+?)!(?P<merge_request_iid>\d+)$"
    ),
    "close_by_merge_request": compile_branch_reset(
        r"^closed via merge request !(?P<merge_request_iid>.+)$",
        r"^status changed to closed by merge request !(?P<merge_request_iid>.+)$",
    ),
    "close_by_commit": compile_branch_reset(
        r"^closed via commit (?P<commit_sha>[a-z0-9]+)$",
        r"^status changed to closed by commit (?P<commit_sha>[a-z0-9]+)$",
    ),
    "restore_source_branch": compile_branch_reset(
        r"^restored source branch `(?P<branch_name>.+)`$",
    ),
    "remove_label": compile_branch_reset(r"^removed ~(?P<label_id>\d+) label$"),
    "add_label": compile_branch_reset(r"^added ~(?P<label_id>\d+) label$"),
    "create_branch": compile_branch_reset(
        r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\).*$"
    ),
    "mark_task_as_incomplete": compile_branch_reset(
        r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as incomplete$"
    ),
    "mark_task_as_done": compile_branch_reset(
        r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as completed$",
    ),
    "add_commits": compile_branch_reset(
        r"added (?P<number_of_commits>\d+)\scommit[s]?\n\n.+(?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)<.*",
        r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)\n)+$",
        r"^added (?P<number_of_commits>\d+) new commit[s]?:\n\n(\* (?P<short_sha>[a-z0-9]{11}) - (?P<title>.+?)\n)+$",
        r"^added (?P<number_of_commits>\d+) commit[s]?(?:.*\n?)*$",
        r"^added 0 new commits:\n\n$",  # seems weird
    ),
    "address_in_merge_request": compile_branch_reset(
        r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"
    ),
    "unmark_as_work_in_progress": compile_branch_reset(
        r"^unmarked as a [*]{2}work in progress[*]{2}$",
        r"^unmarked this merge request as a work in progress$",
    ),
    "mark_as_work_in_progress": compile_branch_reset(
        r"^marked as a [*]{2}work in progress[*]{2}$",
        r"^marked this merge request as a [*]{2}work in progress[*]{2}$",
    ),
    "merge": compile_branch_reset(
        r"^merged$",
        r"^status changed to merged$",
    ),
    "change_description": compile_branch_reset(r"^changed the description$"),
    "change_title": compile_branch_reset(
        r"^changed title from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
        r"^changed title: [*]{2}(?P<old_title>.+)[*]{2} → [*]{2}(?P<new_title>.+)[*]{2}$",
        r"^title changed from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
    ),
    "move_from": compile_branch_reset(
        r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"
    ),
    "move_to": compile_branch_reset(
        r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"
    ),
    "reopen": compile_branch_reset(r"^reopened$", r"^status changed to reopened$"),
    "close": compile_branch_reset(
        r"^closed$",
        r"^status changed to closed$",
    ),
    "unrelate_from_external_issue": compile_branch_reset(
        r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
    ),
    "relate_to_external_issue": compile_branch_reset(
        r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"
    ),
    "unrelate_from_issue": compile_branch_reset(
        r"^removed the relation with #(?P<issue_iid>\d+)$"
    ),
    "relate_to_issue": compile_branch_reset(
        r"^marked this issue as related to #(?P<issue_iid>\d+)$"
    ),
    "has_duplicate": compile_branch_reset(
        r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"
    ),
    "mark_as_duplicate": compile_branch_reset(
        r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"
    ),
    "make_visible": compile_branch_reset(
        r"^made the issue visible to everyone$",
        r"^made the issue visible$",
    ),
    "make_confidential": compile_branch_reset(r"^made the issue confidential$"),
    "remove_weight": compile_branch_reset(r"^removed the weight$"),
    "change_weight": compile_branch_reset(
        r"^changed weight to [*]{2}(?P<weight>\d+)[*]{2}$"
    ),
    "remove_due_date": compile_branch_reset(r"^removed due date$"),
    "change_due_date": compile_branch_reset(
        r"^changed due date to (?P<month>(?:january|february|march|april|may|june|july|august|september|october|november|december)) (?P<day>\d\d), (?P<year>\d{4})$"
    ),
    "remove_time_estimate": compile_branch_reset(r"^removed time estimate$"),
    "change_time_estimate": compile_branch_reset(
        r"^changed time estimate to"
        + r"(?:\s(?P<months>[-]?\d+)mo)?"
        + r"(?:\s(?P<weeks>[-]?\d+)w)?"
        + r"(?:\s(?P<days>[-]?\d+)d)?"
        + r"(?:\s(?P<hours>[-]?\d+)h)?"
        + r"(?:\s(?P<minutes>[-]?\d+)m)?"
        + r"(?:\s(?P<seconds>[-]?\d+)s)?$"
    ),
    "unlock_merge_request": compile_branch_reset(r"^unlocked this merge request$"),
    "lock_merge_request": compile_branch_reset(r"^locked this merge request$"),
    "unlock_issue": compile_branch_reset(r"^unlocked this issue$"),
    "lock_issue": compile_branch_reset(r"^locked this issue$"),
    "remove_spend_time": compile_branch_reset(r"^removed time spent$"),
    "subtract_spend_time": compile_branch_reset(
        r"^subtracted"
        + r"(?:\s(?P<months>\d+)mo)?"
        + r"(?:\s(?P<weeks>\d+)w)?"
        + r"(?:\s(?P<days>\d+)d)?"
        + r"(?:\s(?P<hours>\d+)h)?"
        + r"(?:\s(?P<minutes>\d+)m)?"
        + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
    ),
    "add_spend_time": compile_branch_reset(
        r"^added"
        + r"(?:\s(?P<months>\d+)mo)?"
        + r"(?:\s(?P<weeks>\d+)w)?"
        + r"(?:\s(?P<days>\d+)d)?"
        + r"(?:\s(?P<hours>\d+)h)?"
        + r"(?:\s(?P<minutes>\d+)m)?"
        + r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
    ),
    "remove_milestone": compile_branch_reset(
        r"^removed milestone$", r"^milestone removed$"
    ),
    "change_milestone": compile_branch_reset(
        r"^changed milestone to %(?P<milestone_iid>\d+)$",
        r"^changed milestone to %(?P<milestone_name>.+)$",
        r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_iid>\d+)$",
        r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_name>.+)$",
        r"^milestone changed to %(?P<milestone_iid>\d+)$",
        r"^milestone changed to \[(?P<release_name>.+)\]\((?P<release_link>.+)\)$",
        r"^milestone changed to (?P<release_name>.+)$",
    ),
    "unassign_user": compile_branch_reset(
        r"^unassigned @(?P<user_name>.*)$",
        r"^removed assignee$",
    ),
    "assign_user": compile_branch_reset(r"^assigned to @(?P<user_name>.*)$"),
    "mention_in_external_merge_request": compile_branch_reset(
        r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"
    ),
    "mention_in_merge_request": compile_branch_reset(
        r"^mentioned in merge request !(?P<merge_request_iid>\d+)$",
    ),
    "mention_in_external_commit": compile_branch_reset(
        r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$",
    ),
    "mention_in_commit": compile_branch_reset(
        r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$",
    ),
    "mention_in_external_issue": compile_branch_reset(
        r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$",
    ),
    "mention_in_issue": compile_branch_reset(
        r"^mentioned in issue #(?P<issue_iid>\d+)$",
    ),
    "resolve_threads": compile_branch_reset(r"^resolved all threads$"),
    "approve_merge_request": compile_branch_reset(r"^approved this merge request$"),
    "resolve_all_discussions": compile_branch_reset(
        r"^resolved all discussions$",
    ),
    "unapprove_merge_request": compile_branch_reset(r"^unapproved this merge request$"),
    "automatic_merge_on_pipeline_completion_enabled": compile_branch_reset(
        r"^enabled an automatic merge when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
    ),
    "automatic_merge_on_build_success_enabled": compile_branch_reset(
        r"^enabled an automatic merge when the build for (?P<commit_sha>[0-9a-z]+) succeeds$",
    ),
    "abort_automatic_merge": compile_branch_reset(
        r"^aborted the automatic merge because (?P<abort_reason>[a-z\s]+)$"
    ),
    "cancel_automatic_merge": compile_branch_reset(
        r"^canceled the automatic merge$",
    ),
    "create_issue_from_discussion": compile_branch_reset(
        r"^created #(?P<issue_iid>\d+) to continue this discussion$"
    ),
    "marked_merge_request_ready": compile_branch_reset(
        r"^marked this merge request as \*\*ready\*\*$"
    ),
    "marked_merge_request_note": compile_branch_reset(
        r"^marked this merge request as \*\*draft\*\*$"
    ),
    "requested_review": compile_branch_reset(
        r"^requested review from @(?P<user_name>.*)$",
        r"^requested review from @(?P<user_name>.*) and @(?P<user_name2>.*)$",
    ),
    "cancel_review_request": compile_branch_reset(
        r"^removed review request for @(?P<user_name>.*)$"
    ),
    "mention_in_epic": compile_branch_reset(
        r"^mentioned in epic &(?P<noteable_iid>\d+)$"
    ),
    "reassigned": compile_branch_reset(
        r"^reassigned to @(?P<user_name>.*)$",
    ),
    "merge_request_removed": compile_branch_reset(
        r"^removed this merge request from the merge train because no stages / jobs for this pipeline.$"
    ),
    "merge_train_started": compile_branch_reset(
        r"^started a merge train$",
    ),
    "automatic_add_to_merge_train_enabled": compile_branch_reset(
        r"^enabled automatic add to merge train when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$",
    ),
}


IMPORT_PATTERN: Pattern = compile_branch_reset(
    r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \(imported from gitlab project\)\*",
    r"\*by (?P<pre_import_author>.+) on \d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC \(imported from gitlab project\)\*",
)


def remove_import_pattern(body: str, pattern: Pattern = IMPORT_PATTERN):
    body = body.lower().strip()
    match = pattern.search(body)
    if not match:
        return body, {}
    return pattern.sub(body), match.groupdict()


def classify_annotation(body: str, patterns: dict[str, Pattern] = CLASSIFIERS):
    body = body.lower().strip()
    body, attributes = remove_import_pattern(body)

    matches = {}
    for classifier, pattern in patterns.items():
        match = pattern.search(body)
        if not match:
            continue
        matches[classifier] = match

    classifier = max(matches, key=matches.get, default=DEFAULT)

    if classifier == DEFAULT:
        log.info(f"Unknown system note body: {body}")
    else:
        attributes.update(matches[classifier].groupdict())

    return classifier, attributes


def parse_system_note(note: Note):
    annotator = objects.User(
        name=note.author.get("name"),
        email=note.author.get("email"),
        gitlab_username=note.author.get("username"),
        gitlab_id=note.author.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    annotation_type, kwargs = classify_annotation(note.body)
    return objects.Annotation(
        id=note.id,
        type=annotation_type,
        body=note.body,
        kwargs=kwargs,
        annotator=annotator,
        prov_start=note.created_at,
        prov_end=note.created_at,
    )


def parse_comment(comment: Comment):
    annotator = objects.User(
        name=comment.author.get("name"),
        email=comment.author.get("email"),
        gitlab_username=comment.author.get("username"),
        gitlab_id=comment.author.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return objects.Annotation(
        id=f"{uuid.uuid4()}{annotator.gitlab_id}{abs(hash(comment.note))}",
        type="add_comment",
        body=comment.note,
        annotator=annotator,
        prov_start=comment.created_at,
        prov_end=comment.created_at,
    )


def parse_note(note: Note):
    annotator = objects.User(
        name=note.author.get("name"),
        email=note.author.get("email"),
        gitlab_username=note.author.get("username"),
        gitlab_id=note.author.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return objects.Annotation(
        id=note.id,
        type="add_note",
        body=note.body,
        annotator=annotator,
        prov_start=note.created_at,
        prov_end=note.created_at,
    )


def parse_award(award: AwardEmoji):
    annotator = objects.User(
        name=award.user.get("name"),
        email=award.user.get("email"),
        gitlab_username=award.user.get("username"),
        gitlab_id=award.user.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return objects.Annotation(
        id=award.id,
        type="award_emoji",
        body=award.name,
        annotator=annotator,
        prov_start=award.created_at,
        prov_end=award.created_at,
    )


def parse_label(label: Label):
    annotator = objects.User(
        name=label.user.get("name"),
        email=label.user.get("email"),
        gitlab_username=label.user.get("username"),
        gitlab_id=label.user.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return objects.Annotation(
        id=label.id,
        type=f"{label.action}_label",
        body=label.action,
        annotator=annotator,
        prov_start=label.created_at,
        prov_end=label.created_at,
    )


def choose_parser(parseable: Parseable):
    if isinstance(parseable, Note) and not getattr(parseable, "system", False):
        return parse_note
    elif isinstance(parseable, Note) and getattr(parseable, "system", False):
        return parse_system_note
    elif isinstance(parseable, Comment):
        return parse_comment
    elif isinstance(parseable, Label):
        return parse_label
    elif isinstance(parseable, AwardEmoji):
        return parse_award
    else:
        log.warn(f"no parser found for {parseable=}")
        return


def parse_annotations(parseables: Sequence[Parseable]):
    annotations = []
    for parseable in parseables:
        parser = choose_parser(parseable)
        annotations.append(parser(parseable))
    return sorted(annotations, key=lambda annotation: annotation.prov_start)
