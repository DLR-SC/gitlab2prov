"""
Classify API resources into predefined events.
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

from typing import List, Dict, Any
from prov.constants import PROV_TYPE
from gl2p.utils.objects import Candidates, GL2PEvent
from gl2p.utils.types import Label, Note, Award
from gl2p.utils.helpers import by_date


class SystemNoteEventClassifier:
    """
    A regex based classifier for a single event type.
    """

    def __init__(self, event_type: str, regex: List[str]) -> None:
        """
        Only allow non capturing and named groups in *regex*.
        """

        self.event_type = event_type
        self.patterns = [re.compile(r) for r in regex]

    def matches(self, body: str) -> bool:
        """
        Return whether classifier matches *body*.
        """
        return any(bool(p.search(body)) for p in self.patterns)

    def construct(self, body: str) -> Dict[str, Any]:
        """
        Construct label information from classifier.
        """
        # pick the first pattern that matched
        # is this a potential problem?
        matched = list(filter(bool, map(lambda p: p.search(body), self.patterns)))[0]

        if not matched:
            # should never happen
            return dict()

        info = matched.groupdict()

        return {"event_type": self.event_type, **info}


##############################################################################################################################
#
#   System note event classifiers.
#   A list of possible events can be found in the /docs directory.
#   System note events are marked with a star.
#
##############################################################################################################################


classifiers = [
    SystemNoteEventClassifier(
        event_type="metion_in_issue",
        regex=[r"^mentioned in issue #(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="mention_in_external_issue",
        regex=[r"^mentioned in issue (?P<project_slug>.+)#(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="metion_in_commit",
        regex=[r"^mentioned in commit (?P<commit_sha>[0-9a-z]{40})$"]
    ),
    SystemNoteEventClassifier(
        event_type="mention_in_external_commit",
        regex=[r"^mentioned in commit (?P<project_slug>.+)@(?P<commit_sha>[0-9a-z]{40})$"]
    ),
    SystemNoteEventClassifier(
        event_type="mention_in_merge_request",
        regex=[r"^mentioned in merge request !(?P<merge_request_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="mention_in_external_merge_request",
        regex=[r"^mentioned in merge request (?P<project_slug>.+)!(?P<merge_request_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="assign_user",
        regex=[r"^assigned to @(?P<user_name>.*)$"]
    ),
    SystemNoteEventClassifier(
        event_type="unassign_user",
        regex=[r"^unassigned @(?P<user_name>.*)$"]
    ),
    SystemNoteEventClassifier(
        event_type="change_milestone",
        regex=[
            r"^changed milestone to %(?P<milestone_iid>\d+)$",
            r"^changed milestone to %(?P<milestone_name>.+)$"
        ]
    ),
    SystemNoteEventClassifier(
        event_type="remove_milestone",
        regex=[r"^removed milestone$"]
    ),
    SystemNoteEventClassifier(
        event_type="add_spend_time",
        regex=[(
            r"^added\s" +
            r"(?:(?P<months>\d+)mo\s)?" +
            r"(?:(?P<weeks>\d+)w\s)?" +
            r"(?:(?P<days>\d+)d\s)?" +
            r"(?:(?P<hours>\d+)h\s)?" +
            r"(?:(?P<minutes>\d+)m)?" +
            r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
        )]
    ),
    SystemNoteEventClassifier(
        event_type="subtract_spend_time",
        regex=[(
            r"^subtracted\s" +
            r"(?:(?P<months>\d+)mo\s)?" +
            r"(?:(?P<weeks>\d+)w\s)?" +
            r"(?:(?P<days>\d+)d\s)?" +
            r"(?:(?P<hours>\d+)h\s)?" +
            r"(?:(?P<minutes>\d+)m)?" +
            r"\sof time spent at (?P<date>\d{4}-\d{2}-\d{2})$"
        )]
    ),
    SystemNoteEventClassifier(
        event_type="remove_spend_time",
        regex=[r"^removed time spent$"]
    ),
    SystemNoteEventClassifier(
        event_type="lock_issue",
        regex=[r"^locked this issue$"]
    ),
    SystemNoteEventClassifier(
        event_type="unlock_issue",
        regex=[r"^unlocked this issue$"]
    ),
    SystemNoteEventClassifier(
        event_type="lock_merge_request",
        regex=[r"^locked this merge request$"]
    ),
    SystemNoteEventClassifier(
        event_type="unlock_merge_request",
        regex=[r"^unlocked this merge request$"]
    ),
    SystemNoteEventClassifier(
        event_type="change_time_estimate",
        regex=[(
            r"^changed time estimate to\s" +
            r"(?:(?P<months>\d+)mo\s?)?" +
            r"(?:(?P<weeks>\d+)w\s?)?" +
            r"(?:(?P<days>\d+)d\s?)?" +
            r"(?:(?P<hours>\d+)h\s?)?" +
            r"(?:(?P<minutes>\d+)m)?$"
        )]
    ),
    SystemNoteEventClassifier(
        event_type="remove_time_estimate",
        regex=[r"^removed time estimate$"]
    ),
    SystemNoteEventClassifier(
        event_type="change_due_date",
        regex=[(
            r"^changed due date to\s" +
            r"(?P<month>(?:January|February|March|April|May|June|July|August|September|October|November|December))\s" +
            r"(?P<day>\d\d),\s" +
            r"(?P<year>\d{4})$"
        )]
    ),
    SystemNoteEventClassifier(
        event_type="remove_due_date",
        regex=[r"^removed due date$"]
    ),
    SystemNoteEventClassifier(
        event_type="change_weight",
        regex=[r"^changed weight to \*\*(?P<weight>\d+)\*\*$"]
    ),
    SystemNoteEventClassifier(
        event_type="remove_weight",
        regex=[r"^removed the weight$"]
    ),
    SystemNoteEventClassifier(
        event_type="make_confidential",
        regex=[r"^made the issue confidential$"]
    ),
    SystemNoteEventClassifier(
        event_type="make_visible",
        regex=[r"^made the issue visible to everyone$"]
    ),
    SystemNoteEventClassifier(
        event_type="mark_as_duplicate",
        regex=[r"^marked this issue as a duplicate of #(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="has_duplicate",
        regex=[r"^marked #(?P<issue_iid>\d+) as a duplicate of this issue$"]
    ),
    SystemNoteEventClassifier(
        event_type="relate",
        regex=[r"^marked this issue as related to #(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="unrelate",
        regex=[r"^removed the relation with #(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="relate_external_issue",
        regex=[r"^marked this issue as related to (?P<project_slug>.+)#(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="unrelate_external_issue",
        regex=[r"^removed the relation with (?P<project_slug>.+)#(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="close",
        regex=[
            r"^closed$",
            r"^Status changed to closed$"
        ]
    ),
    SystemNoteEventClassifier(
        event_type="reopen",
        regex=[r"^reopened$"]
    ),
    SystemNoteEventClassifier(
        event_type="move_to",
        regex=[r"^moved to (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="move_from",
        regex=[r"^moved from (?P<project_slug>.*?)#(?P<issue_iid>\d+)$"]
    ),
    SystemNoteEventClassifier(
        event_type="change_title",
        regex=[
            (
                r"^changed title from\s" +
                r"\*\*(?P<old_title>.+)\*\*" +
                r"\sto\s" +
                r"\*\*(?P<new_title>.+)\*\*$"
            ),
            r"^Changed title: \*\*(?P<old_title>.+)\*\* → \*\*(?P<new_title>.+)\*\*$"
        ]
    ),
    SystemNoteEventClassifier(
        event_type="change_description",
        regex=[r"^changed the description$"]
    ),
    SystemNoteEventClassifier(
        event_type="merge",
        regex=[r"^merged$"]
    ),
    SystemNoteEventClassifier(
        event_type="mark_as_work_in_progress",
        regex=[r"^marked as a \*\*Work In Progress\*\*$"]
    ),
    SystemNoteEventClassifier(
        event_type="unmark_as_work_in_progress",
        regex=[r"^unmarked as a \*\*Work In Progress\*\*$"]
    ),
    SystemNoteEventClassifier(
        event_type="address_in_merge_request",
        regex=[r"^created merge request !(?P<merge_request_iid>\d+) to address this issue$"]
    ),
    SystemNoteEventClassifier(
        event_type="add_commits",
        regex=[(
            r"added\s" +
            r"(?P<number_of_commits>\d+)\scommit\n\n" +
            r".*?(?P<short_sha>[a-z0-9]{8})\s-\s" +
            r"(?P<title>.+?).*?\n\n.*"
        )]
    ),
    SystemNoteEventClassifier(
        event_type="mark_task_as_done",
        regex=[r"^marked the task \*\*(?P<task_description>.+)\*\* as completed$"]
    ),
    SystemNoteEventClassifier(
        event_type="create_branch",
        regex=[r"^created branch \[`(?P<branch_name>.+)`\]\((?P<compare_link>.+)\)$"]
    ),
    SystemNoteEventClassifier(
        event_type="add_label",
        regex=[r"^added ~(?P<label_id>\d+) label$"]
    ),
    SystemNoteEventClassifier(
        event_type="remove_label",
        regex=[r"^removed ~(?P<label_id>\d+) label$"]
    ),
    SystemNoteEventClassifier(
        event_type="restore_source_branch",
        regex=[
            r"^restored source branch `(?P<branch_name>.+)`$",
            r"^Restored source branch `(?P<branch_name>.+)`$"
        ]
    )
]


class SystemNoteClassifier:
    """
    Event type classification for system notes.
    """
    def __init__(self) -> None:
        """
        """
        global classifiers
        self.classifiers = classifiers

    def classify(self, body: str) -> Dict[str, Any]:
        """
        Conclude event type by running classifiers on note body.
        """
        # match classifiers, keep the ones that do
        matching = [classifier for classifier in self.classifiers if classifier.matches(body)]

        if not matching:
            raise ValueError((
                f"No classifier matched the system note body: '{body}'.\n" +
                textwrap.dedent("""\
                This can be due to a couple of different reasons:
                1.) The system note body denotes an event for which no classifier exists yet.
                2.) GitLab made changes to it's API, such that an event that was previously covered
                    by classifiers isn't any more.
                3.) A classifier for this event type exists, though is faulty.

                Please open an Issue on GitLab2PROV's GitHub page and copy this error message to the issue description.
                """)
            ))

        if len(matching) > 1:
            raise ValueError(
                f"More than one classifier matched.\
                \nNote body: '{body}'\
                \nMatching classifiers: {[f.event_type for f in matching]}"
            )

        return matching[0].construct(body)


class EventParser:
    """
    Parse event candidates to events.
    """
    def __init__(self) -> None:
        self.classifier: SystemNoteClassifier = SystemNoteClassifier()

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
            "event_type": "add_label" if label_event["action"] == "add" else "remove_label",
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
            "event_type": "award_emoji",
            "award_name": award["name"]
        }
        return event

    def parse_notes(self, notes: List[Note]) -> List[GL2PEvent]:
        """
        Parse notes, differentiate between system and non system notes.
        """
        events = []

        for note in notes:
            if not note:
                continue
            if not note["system"]:
                events.append(self.parse_note(note))
            else:
                events.append(self.parse_system_note(note))

        return events

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
            "event_type": "note",
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
            "system_note_id": note["id"],
            "content": note["body"],
            "noteable_id": note["noteable_id"],
            "noteable_type": note["noteable_type"],
            **self.classifier.classify(note["body"])
        }
        return event
