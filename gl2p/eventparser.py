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
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class GitLabResourceEvent:
    """
    Represents an event occuring on a resource (Commit, Issue, Merge Request).
    """
    identifier: str
    initiator: str
    type: str
    labels: Dict[Any, Any]
    created_at: Optional[datetime] = None


@dataclass
class EventParser:
    """
    Handles classification of resource events.
    """
    @staticmethod
    def parse_note(note):
        """
        Returns GitLabResourceEvent with event type parsed from note.
        """
        if note.get("system"):
            return EventParser.parse_system_note(note)
        return EventParser.parse_non_system_note(note)

    @staticmethod
    def parse_system_note(sysnote):
        """
        Returns GitLabResourceEvent parsed from system note.
        """
        identifier = sysnote.get("id")
        initiator = sysnote.get("author").get("name")
        type_ = "system note"
        labels = {"body": sysnote.get("body")}
        created_at = sysnote.get("created_at")
        return GitLabResourceEvent(identifier, initiator, type_, labels, created_at)

    @staticmethod
    def parse_non_system_note(note):
        """
        Retruns GitLabResourceEvent parsed from non sytem note.
        """
        identifier = note["id"]
        initiator = note["author"]["name"]
        type_ = "note"
        labels = {"body": note["body"]}
        created_at = note.get("created_at")
        return GitLabResourceEvent(identifier, initiator, type_, labels, created_at)
