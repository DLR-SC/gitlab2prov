from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from gl2p.helpers import qname, date

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
        created_at = date(sysnote)
        return GitLabResourceEvent(identifier, initiator, type_, labels, created_at)

    @staticmethod
    def parse_non_system_note(note):

        identifier = note["id"]
        initiator = note["author"]["name"]
        type_ = "note"
        labels = {"body": note["body"]}
        created_at = date(note)
        return GitLabResourceEvent(identifier, initiator, type_, labels, created_at)
