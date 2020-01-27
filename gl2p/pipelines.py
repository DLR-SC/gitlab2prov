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


from dataclasses import InitVar, dataclass
from typing import Any, Tuple

import gl2p.models as models
from gl2p.commons import FileStatus
from gl2p.gitlab import ProjectWrapper
from gl2p.helpers import qname
from gl2p.processor import CommitProcessor, CommitResourceProcessor
from prov.dot import prov_to_dot
from prov.model import ProvDocument


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
