import datetime
from typing import List

from ...utils import ptime
from ...utils.types import Award, Label, Note
from ..meta import Candidates, Initiator, MetaEvent
from .classifier import classify


def parse_label(label_event: Label) -> MetaEvent:
    """
    Parse a single label.
    """
    label = {}
    created_at = label_event["created_at"]
    initiator = Initiator.from_label_event(label_event)

    if label_event["label"]:
        info = {f"label_{key}": val for key, val in label_event["label"].items()}
        label.update(info)
    if label_event["action"] == "add":
        label["event"] = "added_label"
    else:
        label["event"] = "removed_label"
    label["event_id"] = label_event["id"]

    return MetaEvent.create(initiator, created_at, label)


def parse_award(award: Award) -> MetaEvent:
    """
    Parse a single award.
    """
    initiator = Initiator.from_award_emoji(award)
    created_at = award["created_at"]
    label = {
        "event": "award_emoji",
        "event_id": award["id"],
        "award_name": award["name"]
    }
    return MetaEvent.create(initiator, created_at, label)


def parse_note(note: Note) -> MetaEvent:
    """
    Parse a single non system note.
    """
    initiator = Initiator.from_note(note)
    created_at = note["created_at"]
    label = {
        "event": "note",
        "event_id": note["id"],
        "content": note["body"],
        "note_id": note["id"],
        "noteable_type": note["noteable_type"],
        "noteable_iid": note["noteable_iid"],
        "noteable_id": note["noteable_id"],
        "attachment": note["attachment"]
    }
    return MetaEvent.create(initiator, created_at, label)


def parse_system_note(note: Note) -> MetaEvent:
    """
    Parse a single system note.
    Hand over event type determination to SystemNoteClassifier.
    """
    initiator = Initiator.from_note(note)
    created_at = note["created_at"]
    label = {
        "event_id": note["id"],
        "content": note["body"],
        "noteable_id": note["noteable_id"],
        "noteable_type": note["noteable_type"],
        "system_note_id": note["id"],
        **classify(note["body"])
    }
    return MetaEvent.create(initiator, created_at, label)


def parse_labels(labels: List[Label]) -> List[MetaEvent]:
    """
    Parse events from labels.
    """
    res = []
    for label in labels:
        if label:
            res.append(parse_label(label))
    return res


def parse_awards(awards: List[Award]) -> List[MetaEvent]:
    """
    Parse events from awards.
    """
    res = []
    for award in awards:
        if award:
            res.append(parse_award(award))
    return res


def parse_notes(notes: List[Note]) -> List[MetaEvent]:
    """
    Parse notes, differentiate between system and non system notes.
    """
    res = []
    for note in notes:
        if not note:
            continue
        if note["system"]:
            res.append(parse_system_note(note))
        else:
            res.append(parse_note(note))
    return res


def parse(candidates: Candidates) -> List[MetaEvent]:
    """
    Parse events from labels, awards and notes.
    """
    labels, awards, notes, note_awards = candidates

    les = parse_labels(labels)
    aes = parse_awards([*awards, *note_awards])
    nes = parse_notes(notes)

    def by_date(me: MetaEvent) -> datetime.datetime:
        return ptime(me.start_str)

    # sort parsed meta events by start time ascending
    events = sorted([*les, *aes, *nes], key=by_date)
    return events
