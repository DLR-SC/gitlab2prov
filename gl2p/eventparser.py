"""
Regex based event classification.
"""

# Copyright (c) 2019 German Aerospace Center (DLR/SC).
# All rights reserved.
#
# This file is part of gitlab2prov.
# gitlab2prov is licensed under the terms of the MIT License.
# SPDX short Identifier: MIT
#
# You may obtain a copy of the License at:
# https://opensource.org/licenses/MIT
#
# A command line tool to extract provenance data (PROV W3C)
# from GitLab hosted repositories aswell as
# to store the extracted data in a Neo4J database.
#
# code-author: Claas de Boer <claas.deboer@dlr.de>


import re
import textwrap

from typing import List, Dict, Any, Union, Pattern, Match, Tuple, Optional
from prov.constants import PROV_TYPE
from gl2p.utils.objects import Candidates, GL2PEvent
from gl2p.utils.types import Label, Note, Award
from gl2p.utils.helpers import by_date


# Dictionary of classifiers for event types deduced from system notes.
classifiers: Dict[str, List[str]] = {

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
        r"(?P<number_of_commits>\d+)\scommit\n\n" +
        r".*?(?P<short_sha>[a-z0-9]{8}) - " +
        r"(?P<title>.+?).*?\n\n.*"

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
        r"(?:\s(?P<months>\d+)mo)?" +
        r"(?:\s(?P<weeks>\d+)w)?" +
        r"(?:\s(?P<days>\d+)d)?" +
        r"(?:\s(?P<hours>\d+)h)?" +
        r"(?:\s(?P<minutes>\d+)m)?$"

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

        r"^unassigned @(?P<user_name>.*)$"

    ],

    "assign_user": [

        r"^assigned to @(?P<user_name>.*)$"

    ],

    "mention_in_external_merge_request": [

        r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"

    ],

    "mention_in_merge_request": [

        r"^mentioned in merge request !(?P<merge_request_iid>\d+)$"

    ],

    "mention_in_external_commit": [

        r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$"

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
}


import_patterns: List[str] = [

    r"\*By (?P<original_author>.+) on " +
    r"(?P<original_creation_date>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) " +
    r"\(imported from GitLab project\)\*",

    r"\*By (?P<original_author>.+) on " +
    r"(?P<original_creation_date>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\sUTC) " +
    r"\(imported from GitLab project\)\*"

]


# Dictonary of classifiers with compiled patterns
compiled_classifiers: Dict[str, List[Pattern[str]]] = {}


# List of compiled import patterns
compiled_import_patterns: List[Pattern[str]] = []


def compile_regex(regex: str) -> Pattern[str]:
    """
    Wrap re.compile with singular str type rather than type AnyStr.

    Hotfix for overloaded type signature of re.compile.
    """
    return re.compile(regex)


def first_matching_pattern(patterns: List[Pattern[str]], string: str) -> Tuple[Optional[Pattern[str]], Optional[Match[str]]]:
    """
    Return the first pattern of *patterns* that matched *string*.
    """
    for pattern in patterns:
        match = pattern.search(string)
        if match:
            # Matching pattern found
            break
    else:
        # Did not find anything ...
        return None, None

    return pattern, match


def compile_regular_expressions() -> None:
    """
    Compile regular expressions if they havn't been compiled yet.
    """
    global compiled_classifiers
    global compiled_import_patterns

    if not compiled_import_patterns:
        compiled_import_patterns = list(map(compile_regex, import_patterns))

    if not compiled_classifiers:
        compiled_classifiers = {k: list(map(compile_regex, v)) for k, v in classifiers.items()}


def classify(body: str) -> Dict[str, Any]:
    """
    Classify the event that a system note body denotes.
    """
    # Compile regular expressions of import patterns, classifiers
    compile_regular_expressions()

    # Import property label, default is not imported (imported = False)
    import_information: Dict[str, Union[bool, str]] = {"imported": False}

    possible_events: List[Dict[str, Any]] = []

    # Pick first matching pattern
    pattern, match = first_matching_pattern(compiled_import_patterns, body)

    if pattern and match:
        # Pattern matched
        # Strip import information from note body
        body = pattern.split(body)[0].strip()
        # Update import information with matched groups
        import_information = {"imported": True, **match.groupdict()}

    for event, patterns in compiled_classifiers.items():
        # Pick first matching pattern
        pattern, match = first_matching_pattern(patterns, body)

        if not match:
            continue
        # Append to record of possible events
        possible_events.append({"event": event, **match.groupdict()})

    # Raise ValueError if no classifier matched
    # Indicates faulty patterns or an unknown event type

    if not possible_events:
        raise ValueError(
            f"No classifier matched the following system note body:\n\n{body}\n\n" +
            textwrap.fill("Please open an issue on our GitHub page and copy this error message into the issue description.")
        )

    # Raise ValueError when more than one classifier matched
    # Indicates faulty patterns or duplicated classifiers

    if len(possible_events) > 1:
        raise ValueError(
            f"Too many event classifiers matched the following system note body:\n\n{body}\n\n" +
            "The following classifiers matched:\n" +

            "\n".join(
                [
                    f"\t-> {event['event'].upper()} classifier with these groups:\n" +
                    "\n".join(
                        [
                            "\t\tGroup Name: {}\t\tValue: {}".format(k, v)
                            for k, v in event.items()
                            if k != "event"
                        ]
                    )
                    for event in possible_events
                ]
            )
        )

    # Update classified event with import information
    possible_events[0].update(import_information)

    return possible_events[0]


class EventParser:
    """
    Parse event candidates to events.
    """

    def parse(self, candidates: Candidates) -> List[GL2PEvent]:
        """
        Parse events from labels, awards and notes.
        """
        labels, awards, notes, note_awards = candidates

        label_events = self.parse_labels(labels)
        award_events = self.parse_awards([*awards, *note_awards])
        note_events = self.parse_notes(notes)

        return sorted([*label_events, *award_events, *note_events], key=by_date)

    def parse_labels(self, labels: List[Label]) -> List[GL2PEvent]:
        """
        Parse events from labels.
        """
        events = []
        for label in labels:
            if label:
                events.append(self.parse_label(label))
        return events

    def parse_label(self, label_event: Label) -> GL2PEvent:
        """
        Parse a single label.
        """
        event = GL2PEvent()
        event.id = label_event["id"]
        event.initiator = label_event["user"]["name"]
        event.created_at = label_event["created_at"]

        # sometimes the label field seems to have value None
        # avoid erros by providing an empty dict as a default
        label_info = label_event["label"] if label_event.get("label", {}) else {}

        event.label = {
            "event": "add_label" if label_event["action"] == "add" else "remove_label",
            "label_name": label_info.get("name"),
            "label_id": label_info.get("id"),
            "label_color": label_info.get("color"),
            "label_description": label_info.get("description")
        }
        return event

    def parse_awards(self, awards: List[Award]) -> List[GL2PEvent]:
        """
        Parse events from awards.
        """
        events = []
        for award in awards:
            if award:
                events.append(self.parse_award(award))
        return events

    def parse_award(self, award: Award) -> GL2PEvent:
        """
        Parse a single award.
        """
        event = GL2PEvent()
        event.id = award["id"]
        event.initiator = award["user"]["name"]
        event.created_at = award["created_at"]
        event.label = {
            PROV_TYPE: "resource_event",
            "event": "award_emoji",
            "award_name": award["name"]
        }
        return event

    def parse_notes(self, notes: List[Note]) -> List[GL2PEvent]:
        """
        Parse notes, differentiate between system and non system notes.
        """
        return [
            self.parse_system_note(note) if note.get("system") else self.parse_note(note)
            for note in notes
            if note
        ]

    def parse_note(self, note: Note) -> GL2PEvent:
        """
        Parse a single non system note.
        """
        event = GL2PEvent()
        event.id = note["id"]
        event.initiator = note["author"]["name"]
        event.created_at = note["created_at"]
        event.label = {
            PROV_TYPE: "resource_event",
            "event": "note",
            "content": note["body"],
            "note_id": note["id"],
            "noteable_type": note["noteable_type"],
            "noteable_iid": note["noteable_iid"],
            "noteable_id": note["noteable_id"],
            "attachment": note["attachment"]
        }
        return event

    def parse_system_note(self, note: Note) -> GL2PEvent:
        """
        Parse a single system note.
        Hand over event type determination to SystemNoteClassifier.
        """
        event = GL2PEvent()
        event.id = note["id"]
        event.initiator = note["author"]["name"]
        event.created_at = note["created_at"]

        event.label = {
            PROV_TYPE: "resource_event",
            "content": note["body"],
            "noteable_id": note["noteable_id"],
            "noteable_type": note["noteable_type"],
            "system_note_id": note["id"],

            **classify(note["body"])
        }
        return event
