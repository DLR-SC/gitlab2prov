import logging
from dataclasses import dataclass
from typing import TypeVar, Callable

from github.CommitComment import CommitComment
from github.CommitStatus import CommitStatus
from github.Reaction import Reaction
from github.IssueComment import IssueComment
from github.IssueEvent import IssueEvent
from github.TimelineEvent import TimelineEvent
from github.PullRequestComment import PullRequestComment
from github.PullRequestReview import PullRequestReview

from gitlab2prov.domain.objects import Annotation, User
from gitlab2prov.domain.constants import ProvRole

A = TypeVar("A")

log = logging.getLogger(__name__)


@dataclass
class GithubAnnotationParser:
    @staticmethod
    def sort_by_date(annotations: list[Annotation]) -> list[Annotation]:
        return list(sorted(annotations, key=lambda a: a.start))

    def choose_parser(self, raw_annotation: A) -> Callable[[A], Annotation]:
        match raw_annotation:
            case CommitComment():
                return self.parse_commit_comment
            case CommitStatus():
                return self.parse_commit_status
            case Reaction():
                return self.parse_reaction
            case IssueComment():
                return self.parse_issue_comment
            case IssueEvent():
                return self.parse_issue_event
            case TimelineEvent():
                return self.parse_timeline_event
            case PullRequestReview():
                return self.parse_pull_request_review
            case PullRequestComment():
                return self.parse_pull_request_comment
            case _:
                log.warning(f"no parser found for {raw_annotation=}")

    def parse(self, annotations: list[A]) -> list[Annotation]:
        parsed_annotations = []
        for annotation in annotations:
            if parser := self.choose_parser(annotation):
                parsed_annotations.append(parser(annotation))
        return self.sort_by_date(parsed_annotations)

    def parse_commit_comment(self, comment: CommitComment) -> Annotation:
        annotator = User(
            name=comment.user.name,
            email=comment.user.email,
            github_username=comment.user.login,
            github_id=comment.user.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=comment.id,
            name="add_comment",
            body=comment.body,
            start=comment.created_at,
            end=comment.created_at,
            annotator=annotator,
        )

    def parse_commit_status(self, status: CommitStatus) -> Annotation:
        annotator = User(
            name=status.creator.name,
            email=status.creator.email,
            github_username=status.creator.login,
            github_id=status.creator.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=status.id,
            name="add_commit_status",
            body=status.description,
            start=status.created_at,
            end=status.created_at,
            annotator=annotator,
        )

    def parse_reaction(self, reaction: Reaction) -> Annotation:
        annotator = User(
            name=reaction.user.name,
            email=reaction.user.email,
            github_username=reaction.user.login,
            github_id=reaction.user.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=reaction.id,
            name="add_award",
            body=reaction.content,
            start=reaction.created_at,
            end=reaction.created_at,
            annotator=annotator,
        )
            

    def parse_issue_comment(self, comment: IssueComment) -> Annotation:
        annotator = User(
            name=comment.user.name,
            email=comment.user.email,
            github_username=comment.user.login,
            github_id=comment.user.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=comment.id,
            name="add_comment",
            body=comment.body,
            start=comment.created_at,
            end=comment.created_at,
            annotator=annotator,
        )

    def parse_issue_event(self, event: IssueEvent) -> Annotation:
        annotator = User(
            name=event.actor.name,
            email=event.actor.email,
            github_username=event.actor.login,
            github_id=event.actor.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=event.id,
            name=event.event,
            body=event.event,
            start=event.created_at,
            end=event.created_at,
            annotator=annotator,
        )

    def parse_timeline_event(self, event: TimelineEvent) -> Annotation:
        annotator = User(
            name=event.actor.name,
            email=event.actor.email,
            github_username=event.actor.login,
            github_id=event.actor.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=event.id,
            name=event.event,
            body=event.event,
            start=event.created_at,
            end=event.created_at,
            annotator=annotator,
        )

    def parse_pull_request_review(self, review: PullRequestReview) -> Annotation:
        annotator = User(
            name=review.user.name,
            email=review.user.email,
            github_username=review.user.login,
            github_id=review.user.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=review.id,
            name="add_review",
            body=review.body,
            start=review.submitted_at,
            end=review.submitted_at,
            annotator=annotator,
        )

    def parse_pull_request_comment(self, comment: PullRequestComment) -> Annotation:
        annotator = User(
            name=comment.user.name,
            email=comment.user.email,
            github_username=comment.user.login,
            github_id=comment.user.id,
            prov_role=ProvRole.ANNOTATOR,
        )
        return Annotation(
            uid=comment.id,
            name="add_comment",
            body=comment.body,
            start=comment.created_at,
            end=comment.created_at,
            annotator=annotator,
        )
