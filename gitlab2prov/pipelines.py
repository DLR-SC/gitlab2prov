from typing import List, Tuple

from prov.model import ProvDocument

from gitlab2prov.api import GitlabClient
from gitlab2prov.models import create_graph
from gitlab2prov.procs import (CommitProcessor, CommitResourceProcessor,
                        IssueResourceProcessor, MergeRequestResourceProcessor)
from gitlab2prov.procs.meta import CommitModelPackage, ResourceModelPackage
from gitlab2prov.utils.types import (Award, Commit, Diff, Issue, Label, MergeRequest,
                              Note)


class CommitPipeline:
    """
    Pipeline that fetches, processes and models git commits of a project.
    """
    @staticmethod
    async def fetch(client: GitlabClient) -> Tuple[List[Commit], List[Diff]]:
        """
        Retrieve commits and their diffs from the project API wrapper.
        """
        async with client as clt:
            commits = await clt.commits()
            diffs = await clt.commit_diffs()
        return commits, diffs

    @staticmethod
    def process(commits: List[Commit], diffs: List[Diff]) -> List[CommitModelPackage]:
        """
        Return list of commit model packages.
        """
        packages = CommitProcessor.process(commits, diffs)
        return packages

    @staticmethod
    def create_model(packages: List[CommitModelPackage]) -> ProvDocument:
        """
        Return populated PROV graph for resource model.
        """
        model = create_graph(packages)
        return model


class CommitResourcePipeline:
    """
    Pipeline that fetches, processes and models project commits.
    """
    @staticmethod
    async def fetch(client) -> Tuple[List[Commit], List[List[Note]]]:
        """
        Retrieve commits and their notes from the project API wrapped.
        """
        async with client as clt:
            commits = await clt.commits()
            notes = await clt.commit_notes()
        return commits, notes

    @staticmethod
    def process(commits: List[Commit], notes: List[List[Note]]) -> List[ResourceModelPackage]:
        """
        Return list of resource model packages.
        """
        packages = CommitResourceProcessor.process(commits, notes)
        return packages

    @staticmethod
    def create_model(packages: List[ResourceModelPackage]) -> ProvDocument:
        """
        Return populated PROV graph for resource model.
        """
        model = create_graph(packages)
        return model


class IssueResourcePipeline:
    """
    Pipeline that fetches, processes and models project issues.
    """
    @staticmethod
    async def fetch(client) -> Tuple[List[Issue],
                                     List[List[Note]],
                                     List[List[Label]],
                                     List[List[Award]],
                                     List[List[Award]]]:
        """Retrieve issues, their labels, their awards, their notes and
        the awards of all notes from the project API wrapper."""
        async with client as clt:
            issues = await clt.issues()
            labels = await clt.issue_labels()
            awards = await clt.issue_awards()
            notes = await clt.issue_notes()
            note_awards = await clt.issue_note_awards()
        return issues, notes, labels, awards, note_awards

    @staticmethod
    def process(issues: List[Issue],
                notes: List[List[Note]],
                labels: List[List[Label]],
                awards: List[List[Award]],
                note_awards: List[List[Award]]) -> List[ResourceModelPackage]:
        """
        Return list of resource model packages.
        """
        packages = IssueResourceProcessor.process(issues, notes, labels, awards, note_awards)
        return packages

    @staticmethod
    def create_model(packages: List[ResourceModelPackage]) -> ProvDocument:
        """
        Return populated PROV graph for resource model.
        """
        model = create_graph(packages)
        return model


class MergeRequestResourcePipeline:
    """
    Pipeline that fetches, processes and models project merge requests.
    """
    @staticmethod
    async def fetch(client) -> Tuple[List[MergeRequest],
                                     List[List[Note]],
                                     List[List[Label]],
                                     List[List[Award]],
                                     List[List[Award]]]:
        """
        Retrieve merge requests, their labels, their awards, their
        notes and all awards for each note from the project API wrapper.
        """
        async with client as clt:
            merge_requests = await clt.merge_requests()
            labels = await clt.merge_request_labels()
            awards = await clt.merge_request_awards()
            notes = await clt.merge_request_notes()
            note_awards = await clt.merge_request_note_awards()
        return merge_requests, notes, labels, awards, note_awards

    @staticmethod
    def process(merge_requests: List[MergeRequest],
                notes: List[List[Note]],
                labels: List[List[Label]],
                awards: List[List[Award]],
                note_awards: List[List[Award]]) -> List[ResourceModelPackage]:
        """
        Return list of resource model packages.
        """
        packages = MergeRequestResourceProcessor.process(merge_requests, notes, labels, awards, note_awards)
        return packages

    @staticmethod
    def create_model(packages: List[ResourceModelPackage]) -> ProvDocument:
        """
        Return populated PROV graph for resource model.
        """
        model = create_graph(packages)
        return model
