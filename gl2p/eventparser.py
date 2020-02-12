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


from dataclasses import dataclass
from typing import List
from prov.constants import PROV_TYPE
from gl2p.utils.objects import EventCandidates, GL2PEvent
from gl2p.utils.types import Label, Note, Award
from gl2p.utils.helpers import by_date


@dataclass
class EventParser:
    """
    Handles classification of resource events.
    """
    def parse(self, eventables: EventCandidates) -> List[GL2PEvent]:
        """
        Return list of GL2PEvent internals parsed from event candidates of *eventables*.

        A list of possible events can be found in /docs.
        """
        events = []  # type: List[GL2PEvent]

        for label in eventables.labels:
            if not label:
                continue
            events.append(self.parse_label(label))

        for award in [*eventables.awards, *eventables.note_awards]:
            if not award:
                continue
            events.append(self.parse_award(award))

        for note in eventables.notes:
            if not note:
                continue
            events.append(self.parse_note(note))

        return sorted(events, key=by_date)

    @staticmethod
    def parse_label(label: Label) -> GL2PEvent:
        """
        Return GL2PEvent internal parsed from *label*.
        """
        id_ = label["id"]
        initiator = label["user"]["name"]

        if label["action"] == "remove":
            type_ = "remove_label"
        elif label["action"] == "add":
            type_ = "add_label"

        created_at = label["created_at"]

        label = {
            PROV_TYPE: "resource_event",
            "event_type": type_,
            "label_name": label["label"]["name"]
        }
        return GL2PEvent(id_, initiator, label, created_at)

    @staticmethod
    def parse_award(award: Award) -> GL2PEvent:
        """
        Return GL2PEvent internal parsed from *award*.
        """
        id_ = award["id"]
        initiator = award["user"]["name"]
        type_ = "award_emoji"

        label = {
            PROV_TYPE: "resource_event",
            "event_type": type_,
            "awardable_id": award["awardable_id"],
            "awardable_type": award["awardable_type"],
            "award_name": award["name"],
        }

        created_at = award["created_at"]

        return GL2PEvent(id_, initiator, label, created_at)

    def parse_note(self, note: Note) -> GL2PEvent:
        """
        Return GL2PEvent internal parsed from *note*.
        """
        if note["system"]:
            return self.parse_system_note(note)

        return self.parse_non_system_note(note)

    @staticmethod
    def parse_system_note(note: Note) -> GL2PEvent:
        """
        Parse system note to GL2PEvent internal.
        """
        id_ = note["id"]
        initiator = note["author"]["name"]
        created_at = note["created_at"]
        type_ = "system_note"
        label = {PROV_TYPE: "resource_event", "event_type": type_}

        return GL2PEvent(id_, initiator, label, created_at)

    @staticmethod
    def parse_non_system_note(note: Note) -> GL2PEvent:
        """
        Parse non system note to GL2PEvent internal.
        """
        id_ = note["id"]
        initiator = note["author"]["name"]
        created_at = note["created_at"]
        type_ = "note"
        label = {PROV_TYPE: "resource_event", "event_type": type_}

        return GL2PEvent(id_, initiator, label, created_at)
