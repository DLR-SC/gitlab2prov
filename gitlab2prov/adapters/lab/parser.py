import logging
import uuid
from dataclasses import dataclass
from typing import TypeVar, Callable

from gitlab.v4.objects import (
    ProjectIssueNote,
    ProjectMergeRequestNote,
    ProjectCommitComment,
    ProjectIssueResourceLabelEvent,
    ProjectMergeRequestResourceLabelEvent,
    ProjectIssueAwardEmoji,
    ProjectIssueNoteAwardEmoji,
    ProjectMergeRequestAwardEmoji,
    ProjectMergeRequestNoteAwardEmoji,
)

from gitlab2prov.adapters.lab.classifiers import SystemNoteClassifier
from gitlab2prov.domain.objects import Annotation, User
from gitlab2prov.domain.constants import ProvRole


A = TypeVar("A")

log = logging.getLogger(__name__)


@dataclass
class GitlabAnnotationParser:

    classifier: SystemNoteClassifier = SystemNoteClassifier()

    @staticmethod
    def sort_by_date(annotations: list[Annotation]) -> list[Annotation]:
        return list(sorted(annotations, key=lambda a: a.start))

    def choose_parser(self, raw_annotation: A) -> Callable[[A], Annotation]:
        match raw_annotation:
            case ProjectIssueNote(system=True) | ProjectMergeRequestNote(system=True):
                return self.parse_system_note
            case ProjectIssueNote() | ProjectMergeRequestNote():
                return self.parse_note
            case ProjectCommitComment():
                return self.parse_comment
            case ProjectIssueResourceLabelEvent() | ProjectMergeRequestResourceLabelEvent():
                return self.parse_label
            case ProjectIssueAwardEmoji() | ProjectIssueNoteAwardEmoji() | ProjectMergeRequestAwardEmoji() | ProjectMergeRequestNoteAwardEmoji():
                return self.parse_award
            case _:
                log.warning(f"no parser found for {raw_annotation=}")
                return

    def parse(self, annotations: list[A]) -> list[Annotation]:
        parsed_annotations = []
        for annotation in annotations:
            if parser := self.choose_parser(annotation):
                parsed_annotations.append(parser(annotation))
        return self.sort_by_date(parsed_annotations)

    def parse_system_note(self, note: ProjectIssueNote | ProjectMergeRequestNote) -> Annotation:
        annotator = User(
            name=note.author.get("name"),
            email=note.author.get("email"),
            gitlab_username=note.author.get("username"),
            gitlab_id=note.author.get("id"),
            prov_role=ProvRole.ANNOTATOR,
        )
        annotation_name, key_value_pairs = self.classifier.classify(note.body)
        return Annotation(
            uid=note.id,
            name=annotation_name,
            body=note.body,
            start=note.created_at,
            end=note.created_at,
            captured_kwargs=key_value_pairs,
            annotator=annotator,
        )

    def parse_comment(self, comment: ProjectCommitComment) -> Annotation:
        annotator = User(
            name=comment.author.get("name"),
            email=comment.author.get("email"),
            gitlab_username=comment.author.get("username"),
            gitlab_id=comment.author.get("id"),
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=f"{uuid.uuid4()}{annotator.gitlab_id}{abs(hash(comment.note))}",
            name="add_comment",
            body=comment.note,
            start=comment.created_at,
            end=comment.created_at,
            annotator=annotator,
        )

    def parse_note(self, note: ProjectIssueNote | ProjectMergeRequestNote) -> Annotation:
        annotator = User(
            name=note.author.get("name"),
            email=note.author.get("email"),
            gitlab_username=note.author.get("username"),
            gitlab_id=note.author.get("id"),
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=note.id,
            name="add_note",
            body=note.body,
            annotator=annotator,
            start=note.created_at,
            end=note.created_at,
        )

    def parse_award(
        self,
        award: ProjectIssueAwardEmoji
        | ProjectIssueNoteAwardEmoji
        | ProjectMergeRequestAwardEmoji
        | ProjectMergeRequestNoteAwardEmoji,
    ) -> Annotation:
        annotator = User(
            name=award.user.get("name"),
            email=award.user.get("email"),
            gitlab_username=award.user.get("username"),
            gitlab_id=award.user.get("id"),
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=award.id,
            name="add_award",
            body=award.name,
            annotator=annotator,
            start=award.created_at,
            end=award.created_at,
        )

    def parse_label(
        self, label: ProjectIssueResourceLabelEvent | ProjectMergeRequestResourceLabelEvent
    ) -> Annotation:
        annotator = User(
            name=label.user.get("name"),
            email=label.user.get("email"),
            gitlab_username=label.user.get("username"),
            gitlab_id=label.user.get("id"),
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=label.id,
            name=f"{label.action}_label",
            body=label.action,
            annotator=annotator,
            start=label.created_at,
            end=label.created_at,
        )
