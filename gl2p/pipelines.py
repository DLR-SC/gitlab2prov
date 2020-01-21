from dataclasses import dataclass, InitVar
from prov.model import ProvDocument
from prov.dot import prov_to_dot
from typing import Tuple, Any

import gl2p.models as models
from gl2p.helpers import qname
from gl2p.gitlab import ProjectWrapper
from gl2p.commons import FileStatus
from gl2p.processor import CommitProcessor, CommitResourceProcessor

@dataclass
class Pipeline:

    client: ProjectWrapper


@dataclass
class CommitPipeline(Pipeline):

    async def fetch(self):
        """
        Get commits and commit diffs asynchronously.
        """

        async with self.client as client:
            commits = await client.commits()
            diffs = await client.commit_diffs()

        return commits, diffs

    def process(self, commits, diffs):
        """
        Process commits and diffs.
        """
        return CommitProcessor(self.client.project_id).run(commits, diffs)

    def create_model(self, resources: Any):
        """
        Create Model from commit objects.
        """

        model = models.Commit(self.client.project_id)

        for commit in resources:
            model.push(commit)

        return model.document()

@dataclass
class CommitResourcePipeline:

    client: ProjectWrapper

    async def fetch(self):
        """
        Fetch commits and commit notes from gitlab client.
        """

        async with self.client as client:

            commits = await client.commits()
            notes = await client.commit_notes()

        return commits, notes

    def process(self, commits, notes):
        """
        Process commits and notes into commitable PROVNodes.
        """
        
        return CommitResourceProcessor(self.client.project_id).run(commits, notes)

    def create_model(self, resources):
        """
        Create commit resource model from commitable PROVNodes.
        """

        model = models.CommitResource(self.client.project_id)

        for commit in resources:
            model.push(commit)

        return model.document()
