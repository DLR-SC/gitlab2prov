import logging
import uuid
from typing import Callable, Sequence
from typing import TypeAlias

from gitlab.v4.objects import ProjectCommitComment
from gitlab.v4.objects import ProjectIssueAwardEmoji
from gitlab.v4.objects import ProjectIssueNote
from gitlab.v4.objects import ProjectIssueNoteAwardEmoji
from gitlab.v4.objects import ProjectIssueResourceLabelEvent
from gitlab.v4.objects import ProjectMergeRequestAwardEmoji
from gitlab.v4.objects import ProjectMergeRequestNote
from gitlab.v4.objects import ProjectMergeRequestNoteAwardEmoji
from gitlab.v4.objects import ProjectMergeRequestResourceLabelEvent

from gitlab2prov.adapters.fetch.annotations import CLASSIFIERS
from gitlab2prov.adapters.fetch.annotations import IMPORT_STATEMENT
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import Annotation
from gitlab2prov.domain.objects import User


log = logging.getLogger(__name__)


DEFAULT = "default_annotation"


Note: TypeAlias = ProjectIssueNote | ProjectMergeRequestNote
Comment: TypeAlias = ProjectCommitComment
AwardEmoji: TypeAlias = (
    ProjectIssueAwardEmoji
    | ProjectIssueNoteAwardEmoji
    | ProjectMergeRequestAwardEmoji
    | ProjectMergeRequestNoteAwardEmoji
)
Label: TypeAlias = (
    ProjectIssueResourceLabelEvent | ProjectMergeRequestResourceLabelEvent
)


def normalize(string: str):
    return string.strip().lower()


def max_munch(string: str):
    matches = []
    for classifier in CLASSIFIERS:
        log.debug(f"trying {classifier=}")
        if classifier.matches(string):
            log.debug(f"match found with {classifier}")
            matches.append(classifier)
    m = max(matches, default=None)
    return m


def classify_system_note(string: str):
    string = normalize(string)
    kwargs = {}

    # remove import statement, if present
    if IMPORT_STATEMENT.matches(string):
        string = IMPORT_STATEMENT.replace(string)
        kwargs = IMPORT_STATEMENT.groupdict()

    # find matching classifier by max_munch
    if classifier := max_munch(string):
        kwargs.update(classifier.groupdict())
        log.debug(f"KWARGS updated with {classifier.groupdict()}")
        return classifier.name, kwargs

    return DEFAULT, kwargs


def parse_system_note(note: Note):
    annotator = User(
        name=note.author.get("name"),
        email=note.author.get("email"),
        gitlab_username=note.author.get("username"),
        gitlab_id=note.author.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    annotation_type, kwargs = classify_system_note(note.body)
    return Annotation(
        id=note.id,
        type=annotation_type,
        body=note.body,
        kwargs=kwargs,
        annotator=annotator,
        prov_start=note.created_at,
        prov_end=note.created_at,
    )


def parse_comment(comment: Comment):
    annotator = User(
        name=comment.author.get("name"),
        email=comment.author.get("email"),
        gitlab_username=comment.author.get("username"),
        gitlab_id=comment.author.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return Annotation(
        id=f"{uuid.uuid4()}{annotator.gitlab_id}{abs(hash(comment.note))}",
        type="add_comment",
        body=comment.note,
        annotator=annotator,
        prov_start=comment.created_at,
        prov_end=comment.created_at,
    )


def parse_note(note: Note):
    annotator = User(
        name=note.author.get("name"),
        email=note.author.get("email"),
        gitlab_username=note.author.get("username"),
        gitlab_id=note.author.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return Annotation(
        id=note.id,
        type="add_note",
        body=note.body,
        annotator=annotator,
        prov_start=note.created_at,
        prov_end=note.created_at,
    )


def parse_award(award: AwardEmoji):
    annotator = User(
        name=award.user.get("name"),
        email=award.user.get("email"),
        gitlab_username=award.user.get("username"),
        gitlab_id=award.user.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return Annotation(
        id=award.id,
        type="award_emoji",
        body=award.name,
        annotator=annotator,
        prov_start=award.created_at,
        prov_end=award.created_at,
    )


def parse_label(label: Label):
    annotator = User(
        name=label.user.get("name"),
        email=label.user.get("email"),
        gitlab_username=label.user.get("username"),
        gitlab_id=label.user.get("id"),
        prov_role=ProvRole.ANNOTATOR,
    )
    return Annotation(
        id=label.id,
        type=f"{label.action}_label",
        body=label.action,
        annotator=annotator,
        prov_start=label.created_at,
        prov_end=label.created_at,
    )


def choose_parser(
    parseable: Note | Comment | AwardEmoji | Label,
) -> Callable[[Note | Comment | AwardEmoji | Label], Annotation] | None:
    match parseable:
        case ProjectIssueNote(system=True) | ProjectMergeRequestNote(system=True):
            return parse_system_note
        case ProjectIssueNote() | ProjectMergeRequestNote():
            return parse_note
        case ProjectCommitComment():
            return parse_comment
        case ProjectIssueResourceLabelEvent() | ProjectMergeRequestResourceLabelEvent():
            return parse_label
        case ProjectIssueAwardEmoji() | ProjectIssueNoteAwardEmoji() | ProjectMergeRequestAwardEmoji() | ProjectMergeRequestNoteAwardEmoji():
            return parse_award
        case _:
            log.warning(f"no parser found for {parseable=}")
            return


def parse_annotations(parseables: Sequence[Note | Comment | AwardEmoji | Label]):
    annotations = []
    for parseable in parseables:
        if parser := choose_parser(parseable):
            annotations.append(parser(parseable))
    return sorted(annotations, key=lambda annotation: annotation.prov_start)
