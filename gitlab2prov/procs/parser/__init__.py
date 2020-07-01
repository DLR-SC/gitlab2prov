import datetime
from typing import List, Optional

from gitlab2prov.utils import p_time
from gitlab2prov.utils.types import Award, Label, Note
from gitlab2prov.procs.meta import Initiator, MetaEvent
from gitlab2prov.procs.parser.classifier import classify


def parse(notes=None, labels=None, awards=None, note_awards=None) -> List[MetaEvent]:
    """
    Parse events from labels, awards and notes.
    """
    if labels is None:
        labels = []
    if awards is None:
        awards = []
    if notes is None:
        notes = []
    if note_awards is None:
        note_awards = []

    s_notes = [n for n in notes if n["system"]]
    n_notes = [n for n in notes if not n["system"]]

    parsed = []
    parsed.extend(map(parse_note, n_notes))
    parsed.extend(map(parse_label, labels))
    parsed.extend(map(parse_award, awards))
    parsed.extend(map(parse_award, note_awards))
    parsed.extend(map(parse_system_note, s_notes))

    parsed = [event for event in parsed if event is not None]

    sorted_parsed = list(sorted(parsed, key=by_date))
    return sorted_parsed


def by_date(meta_event: MetaEvent) -> datetime.datetime:
    """
    Return parsed datetime object from datetime string.
    """
    return p_time(meta_event.started_at)


def parse_label(label: Label) -> MetaEvent:
    """
    Parse a single label.
    """
    attributes = {}
    attributes["event_id"] = label["id"]
    attributes["event"] = "added_label" if label["action"] == "add" else "removed_label"

    initiator = Initiator.from_label(label)

    description = label["label"]

    if not description:
        return MetaEvent.create(initiator, label["created_at"], attributes)

    for key, value in description.items():
        attributes[f"label_{key}"] = value

    return MetaEvent.create(initiator, label["created_at"], attributes)


def parse_award(award: Award) -> MetaEvent:
    """
    Parse a single award.
    """
    attributes = {}
    attributes["event"] = "award_emoji"
    attributes["event_id"] = award["id"]
    attributes["award_name"] = award["name"]

    initiator = Initiator.from_award(award)

    return MetaEvent.create(initiator, award["created_at"], attributes)


def parse_note(note: Note) -> MetaEvent:
    """
    Parse a single non system note.
    """
    attributes = {}
    attributes["event"] = "note"
    attributes["note_id"] = note["id"]
    attributes["content"] = note["body"]
    attributes["event_id"] = note["id"]
    attributes["noteable_id"] = note["noteable_id"]
    attributes["noteable_iid"] = note["noteable_iid"]
    attributes["noteable_type"] = note["noteable_type"]
    attributes["attachment"] = note["attachment"]

    initiator = Initiator.from_note(note)

    return MetaEvent.create(initiator, note["created_at"], attributes)


def parse_system_note(note: Note) -> Optional[MetaEvent]:
    """
    Parse a single system note.

    Event classification handled by classifier.
    """
    if "label" in note["body"]:
        # ignore all label related notes
        # as they get parsed in label events
        # this avoids duplicated label events
        return None

    attributes = {}
    attributes["event_id"] = note["id"]
    attributes["body"] = note["body"]
    attributes["noteable_id"] = note["noteable_id"]
    attributes["noteable_type"] = note["noteable_type"]
    attributes["system_node_id"] = note["id"]

    event_attributes = classify(note)
    attributes.update(event_attributes)

    initiator = Initiator.from_note(note)

    return MetaEvent.create(initiator, note["created_at"], attributes)
