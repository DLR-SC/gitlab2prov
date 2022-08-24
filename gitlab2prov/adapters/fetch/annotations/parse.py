import logging
import operator
import uuid
from typing import Callable
from typing import Sequence
from typing import TypeAlias
from typing import Any

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
from gitlab2prov.adapters.fetch.annotations import AnnotationClassifier
from gitlab2prov.domain.constants import ProvRole
from gitlab2prov.domain.objects import Annotation
from gitlab2prov.domain.objects import User


log = logging.getLogger(__name__)


DEFAULT = "default_annotation"


Comment: TypeAlias = ProjectCommitComment
Note: TypeAlias = ProjectIssueNote | ProjectMergeRequestNote
Label: TypeAlias = (
    ProjectIssueResourceLabelEvent | ProjectMergeRequestResourceLabelEvent
)
AwardEmoji: TypeAlias = (
    ProjectIssueAwardEmoji
    | ProjectIssueNoteAwardEmoji
    | ProjectMergeRequestAwardEmoji
    | ProjectMergeRequestNoteAwardEmoji
)


def normalize(string: str) -> str:
    return string.strip().lower()


def longest_matching_classifier(string: str) -> AnnotationClassifier | None:
    matching = (cls for cls in CLASSIFIERS if cls.matches(string))
    return max(matching, key=len, default=None)


def classify_system_note(string: str) -> tuple[str, dict[str, Any]]:
    string = normalize(string)
    kwargs = {}
    # remove import statement, if present
    if IMPORT_STATEMENT.matches(string):
        string = IMPORT_STATEMENT.replace(string)
        kwargs = IMPORT_STATEMENT.groupdict()
    # find classifier by choosing the one with the longest match
    if classifier := longest_matching_classifier(string):
        kwargs.update(classifier.groupdict())
        return classifier.name, kwargs
    return DEFAULT, kwargs


def parse_system_note(note: Note) -> Annotation:
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


def parse_comment(comment: Comment) -> Annotation:
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


def parse_note(note: Note) -> Annotation:
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


def parse_award(award: AwardEmoji) -> Annotation:
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


def parse_label(label: Label) -> Annotation:
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


def parse_annotations(parseables: Sequence[Note | Comment | AwardEmoji | Label]) -> Sequence[Annotation]:
    annotations = []
    for parseable in parseables:
        if parser := choose_parser(parseable):
            annotations.append(parser(parseable))
    return sorted(annotations, key=operator.attrgetter("prov_start"))
