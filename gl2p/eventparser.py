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
<<<<<<< HEAD
from typing import Any, Dict, Optional

from gl2p.helpers import date, qname

=======
>>>>>>> c719a3197b6a6b3cfa24ec51e62373303167dc5b

@dataclass
class GitLabResourceEvent:

    identifier: str
    initiator: str
    type: str
    labels: Dict[Any, Any]
    created_at: Optional[datetime] = None


@dataclass
class EventParser:

    @staticmethod
    def parse_note(note):
        if note.get("system"):
            return EventParser.parse_system_note(note)
        return EventParser.parse_non_system_note(note)

    @staticmethod
    def parse_system_note(sysnote):
        
        identifier = sysnote.get("id")
        initiator = sysnote.get("author").get("name")  # TODO: match this with real user accounts
        type_ = "system note"
        labels = {"body": sysnote.get("body")} 
        created_at = sysnote.get("created_at")
        return GitLabResourceEvent(identifier, initiator, type_, labels, created_at)

    @staticmethod
    def parse_non_system_note(note):

        identifier = note["id"]
        initiator = note["author"]["name"]
        type_ = "note"
        labels = {"body": note["body"]}
        created_at = note.get("created_at")
        return GitLabResourceEvent(identifier, initiator, type_, labels, created_at)
