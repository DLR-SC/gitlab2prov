import re
from functools import lru_cache
from typing import Any, Dict, List, Pattern
from gitlab2prov.utils.types import Note


classifiers: Dict[str, List[str]] = {

    "change_target_branch": [
        r"^changed target branch from `(?P<old_target_branch>.+)` to `(?P<new_target_branch>.+)`$"
    ],

    "change_epic": [

        r"^changed epic to &(?P<epic_iid>\d+)$",
        r"^changed epic to &(?P<epic_name>.+)$",
        r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>\d+)$",
        r"^changed epic to (?P<project_slug>.+)&(?P<epic_name>.+)$"

    ],

    "remove_from_external_epic": [

        r"^removed from epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
        r"^removed from epic (?P<project_slug>.+)&(?P<epic_name>.+)$"

    ],

    "add_to_external_epic": [

        r"^added to epic (?P<project_slug>.+)&(?P<epic_iid>\d+)$",
        r"^added to epic (?P<project_slug>.+)&(?P<epic_name>.+)$"

    ],

    "remove_from_epic": [

        r"^removed from epic &(?P<epic_iid>\d+)$",
        r"^removed from epic &(?P<epic_name>.+)$"

    ],

    "add_to_epic": [

        r"^added to epic &(?P<epic_iid>\d+)$",
        r"^added to epic &(?P<epic_name>.+)$"

    ],

    "close_by_external_commit": [

        r"^closed via commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]+)$"

    ],

    "close_by_external_merge_request": [

        r"^close via merge request (?P<project_slug>.+?)!(?P<merge_request_iid>\d+)$"

    ],

    "close_by_merge_request": [

        r"^closed via merge request !(?P<merge_request_iid>.+)$"

    ],

    "close_by_commit": [

        r"^closed via commit (?P<commit_sha>[a-z0-9]+)$"

    ],

    "restore_source_branch": [

        r"^restored source branch `(?P<branch_name>.+)`$",
        r"^Restored source branch `(?P<branch_name>.+)`$"

    ],

    "remove_label": [

        r"^removed ~(?P<label_id>\d+) label$"

    ],

    "add_label": [

        r"^added ~(?P<label_id>\d+) label$"

    ],

    "create_branch": [
        r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\).*$"
    ],

    "mark_task_as_incomplete": [

        r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as incomplete$"

    ],

    "mark_task_as_done": [

        r"^marked the task [*]{2}(?P<task_description>.+)[*]{2} as completed$"

    ],

    "add_commits": [

        r"added " +
        r"(?P<number_of_commits>\d+)\scommit[s]?\n\n" +
        r".+(?P<short_sha>[a-z0-9]{8}) - (?P<title>.+?)<.*",

        r"^added (?P<number_of_commits>\d+) commit[s]?(?:.*\n?)*$",

    ],

    "address_in_merge_request": [

        r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"

    ],

    "unmark_as_work_in_progress": [

        r"^unmarked as a [*]{2}Work In Progress[*]{2}$"

    ],

    "mark_as_work_in_progress": [

        r"^marked as a [*]{2}Work In Progress[*]{2}$"

    ],

    "merge": [

        r"^merged$"

    ],

    "change_description": [

        r"^changed the description$"

    ],

    "change_title": [

        r"^changed title from [*]{2}(?P<old_title>.+)[*]{2} to [*]{2}(?P<new_title>.+)[*]{2}$",
        r"^Changed title: [*]{2}(?P<old_title>.+)[*]{2} → [*]{2}(?P<new_title>.+)[*]{2}$"

    ],

    "move_from": [

        r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"

    ],

    "move_to": [

        r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"

    ],

    "reopen": [

        r"^reopened$"

    ],

    "close": [

        r"^closed$",
        r"^Status changed to closed$"

    ],

    "unrelate_from_external_issue": [

        r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"

    ],

    "relate_to_external_issue": [

        r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"

    ],

    "unrelate_from_issue": [

        r"^removed the relation with #(?P<issue_iid>\d+)$"

    ],

    "relate_to_issue": [

        r"^marked this issue as related to #(?P<issue_iid>\d+)$"

    ],

    "has_duplicate": [

        r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"

    ],

    "mark_as_duplicate": [

        r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"

    ],

    "make_visible": [

        r"^made the issue visible to everyone$"

    ],

    "make_confidential": [

        r"^made the issue confidential$"

    ],

    "remove_weight": [

        r"^removed the weight$"

    ],

    "change_weight": [

        r"^changed weight to [*]{2}(?P<weight>\d+)[*]{2}$"

    ],

    "remove_due_date": [

        r"^removed due date$"

    ],

    "change_due_date": [

        r"^changed due date to " +
        r"(?P<month>(?:January|February|March|April|May|June|July|August|September|October|November|December)) " +
        r"(?P<day>\d\d), " +
        r"(?P<year>\d{4})$"

    ],

    "remove_time_estimate": [

        r"^removed time estimate$"

    ],

    "change_time_estimate": [

        r"^changed time estimate to" +
        r"(?:\s(?P<months>[-]?\d+)mo)?" +
        r"(?:\s(?P<weeks>[-]?\d+)w)?" +
        r"(?:\s(?P<days>[-]?\d+)d)?" +
        r"(?:\s(?P<hours>[-]?\d+)h)?" +
        r"(?:\s(?P<minutes>[-]?\d+)m)?" +
        r"(?:\s(?P<seconds>[-]?\d+)s)?$"

    ],

    "unlock_merge_request": [

        r"^unlocked this merge request$"

    ],

    "lock_merge_request": [

        r"^locked this merge request$"

    ],

    "unlock_issue": [

        r"^unlocked this issue$"

    ],

    "lock_issue": [

        r"^locked this issue$"

    ],

    "remove_spend_time": [

        r"^removed time spent$"

    ],

    "subtract_spend_time": [

        r"^subtracted" +
        r"(?:\s(?P<months>\d+)mo)?" +
        r"(?:\s(?P<weeks>\d+)w)?" +
        r"(?:\s(?P<days>\d+)d)?" +
        r"(?:\s(?P<hours>\d+)h)?" +
        r"(?:\s(?P<minutes>\d+)m)?" +
        r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"

    ],

    "add_spend_time": [

        r"^added" +
        r"(?:\s(?P<months>\d+)mo)?" +
        r"(?:\s(?P<weeks>\d+)w)?" +
        r"(?:\s(?P<days>\d+)d)?" +
        r"(?:\s(?P<hours>\d+)h)?" +
        r"(?:\s(?P<minutes>\d+)m)?" +
        r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"

    ],

    "remove_milestone": [

        r"^removed milestone$"

    ],

    "change_milestone": [

        r"^changed milestone to %(?P<milestone_iid>\d+)$",
        r"^changed milestone to %(?P<milestone_name>.+)$",
        r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_iid>\d+)$",
        r"^changed milestone to (?P<project_slug>.+)%(?P<milestone_name>.+)$"

    ],

    "unassign_user": [

        r"^unassigned @(?P<user_name>.*)$",

        r"^removed assignee$",

    ],

    "assign_user": [

        r"^assigned to @(?P<user_name>.*)$"

    ],

    "mention_in_external_merge_request": [

        r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"

    ],

    "mention_in_merge_request": [

        r"^mentioned in merge request !(?P<merge_request_iid>\d+)$",
        r"^Mentioned in merge request !(?P<merge_request_iid>\d+)$"

    ],


    "mention_in_external_commit": [

        r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$",
        r"^Mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$"

    ],

    "mention_in_commit": [

        r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$"

    ],

    "mention_in_external_issue": [

        r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$"

    ],

    "mention_in_issue": [

        r"^mentioned in issue #(?P<issue_iid>\d+)$"

    ],

    "resolve_threads": [

        r"^resolved all threads$"

    ],

    "approve_merge_request": [

        r"^approved this merge request$"

    ],

    "resolve_all_discussions": [

        r"^resolved all discussions$"

    ],

    "unapprove_merge_request": [

        r"^unapproved this merge request$"

    ],

    "enable_automatic_merge_on_pipeline_completion": [

        r"^enabled an automatic merge when the pipeline for (?P<pipeline_commit_sha>[0-9a-z]+) succeeds$"

    ],

    "abort_automatic_merge": [

        r"^aborted the automatic merge because (?P<abort_reason>[a-z\s]+)$"

    ],

    "cancel_automatic_merge": [

        r"^canceled the automatic merge$"

    ],

    "create_issue_from_discussion": [

        r"^created #(?P<issue_iid>\d+) to continue this discussion$"

    ],

    "marked_merge_request_ready": [

        r"^marked this merge request as \*\*ready\*\*$"

    ],

    "marked_merge_request_note": [

        r"^marked this merge request as \*\*draft\*\*$  "
    ],

    "requested_review": [

        r"^requested review from @(?P<user_name>.*)$",
        r"^requested review from @(?P<user_name>.*) and @(?P<user_name2>.*)$"

    ],

    "cancel_review_request": [
    
        r"^removed review request for @(?P<user_name>.*)$"

    ],

    "mention_in_epic": [

        r"^mentioned in epic &(?P<noteable_iid>\d+)$"

    ],



}


import_patterns: List[str] = [

    r"\*By (?P<original_author>.+) on " +
    r"(?P<original_creation_date>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) " +
    r"\(imported from GitLab project\)\*",

    r"\*By (?P<original_author>.+) on " +
    r"(?P<original_creation_date>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC) " +
    r"\(imported from GitLab project\)\*"

]


@lru_cache()
def compiled_import_patterns() -> List[Pattern[str]]:
    """
    Compile import patterns on first call.

    All successive calls get the cached return value of the first call.
    """
    compiled = []
    for pattern in import_patterns:
        compiled.append(re.compile(pattern))
    return compiled


@lru_cache()
def compiled_classifiers() -> Dict[str, List[Pattern[str]]]:
    """
    Compile classifier patterns on first call.

    All successive calls get the cached return value of the first call.
    """
    compiled = {}
    for event, patterns in classifiers.items():
        compiled[event] = [re.compile(pattern) for pattern in patterns]
    return compiled


def classify(note: Note) -> Dict[str, Any]:
    """
    Return attributes for a note by running it through classifiers.
    """
    if note["type"] == "DiffNote":
        return diff_note_attributes(note)

    matches = event_attributes(note["body"])

    if not matches:
        raise Exception(f"No match found for body: '{note['body']}' of note: <{note}>.")
    if len(matches) > 2:
        raise Exception(f"More than one match for body : '{note['body']}' of note: <{note}>.")

    attributes = {}
    attributes.update(matches[0])
    attributes.update(import_attributes(note["body"]))

    return attributes


def diff_note_attributes(note: Note) -> Dict[str, Any]:
    """
    Return attributes for a diff note.
    """
    attributes = {}
    attributes["event"] = "changed_lines"

    position = note["position"]
    attributes["position_type"] = position["position_type"]
    attributes["position_base_sha"] = position["base_sha"]
    attributes["position_new_line"] = position["new_line"]
    attributes["position_old_line"] = position["old_line"]
    attributes["position_head_sha"] = position["head_sha"]
    attributes["position_old_path"] = position["old_path"]
    attributes["position_new_path"] = position["new_path"]
    attributes["position_start_sha"] = position["start_sha"]

    return attributes


def event_attributes(body: str) -> List[Dict[str, Any]]:
    """
    Run all patterns against the note body.

    Record all that match and return their event type aswell as the matched groups.
    """
    attribute_list = []
    for event_name, regex_list in compiled_classifiers().items():
        for regex in regex_list:
            match_found = regex.search(body)
            if not match_found:
                continue
            attributes = {"event": event_name}
            attributes.update(match_found.groupdict())
            attribute_list.append(attributes)
            break
    return attribute_list


def import_attributes(body: str) -> Dict[str, Any]:
    """
    Match note body against import patterns to find out whether it was imported or not.
    """
    attributes = {}
    for import_regex in compiled_import_patterns():
        match_found = import_regex.search(body)
        if match_found:
            attributes["imported"] = True
            attributes.update(match_found.groupdict())
            break
    else:
        attributes["imported"] = False
    return attributes
