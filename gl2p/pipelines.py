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

from typing import List, Tuple
from dataclasses import dataclass
from prov.model import ProvDocument
from gl2p.api.gitlab import GitLabProjectWrapper
from gl2p.processor import (CommitProcessor, CommitResourceProcessor,
                            IssueResourceProcessor, MergeRequestResourceProcessor)
from gl2p.models import CommitModel, CommitResourceModel, ResourceModel
from gl2p.utils.objects import Resource, ParseableContainer, CommitResource
from gl2p.utils.types import Commit, Issue, MergeRequest, Diff


@dataclass
class CommitPipeline:
    """
    Pipeline that fetches, processes and models git commits of a project.
    """
    project_id: str
    api_client: GitLabProjectWrapper

    async def fetch(self) -> Tuple[List[Commit], List[Diff]]:
        """
        Retrieve commits and their diffs from the project API wrapper.
        """
        async with self.api_client as client:
            commits = await client.commits()
            diffs = await client.commit_diffs()

        return commits, diffs

    def process(self, commits: List[Commit], diffs: List[Diff]) -> List[CommitResource]:
        """
        Return list of internal PROV-DM groupings.

        Precompute id's, activities, entities, agents and labels.
        """
        processor = CommitProcessor(self.project_id)
        return processor.run(commits, diffs)

    def create_model(self, resources: List[CommitResource]) -> ProvDocument:
        """
        Return PROV document containing commit model populated with
        PROV-DM groupings.
        """
        model = CommitModel(self.project_id)

        for resource in resources:
            model.push(resource)

        return model.document()


@dataclass
class CommitResourcePipeline:
    """
    Pipeline that fetches, processes and models project commits.
    """
    project_id: str
    api_client: GitLabProjectWrapper

    async def fetch(self) -> Tuple[List[Commit], ParseableContainer]:
        """
        Retrieve commits and their notes from the project API wrapper.
        """
        async with self.api_client as client:
            commits = await client.commits()
            notes = await client.commit_notes()

        return commits, ParseableContainer(notes=notes)

    def process(self, commits: List[Commit], event_candidates: ParseableContainer) -> List[Resource]:
        """
        Return list of internal PROV-DM groupings.

        Precompute id's, activities, entities, agents and labels.
        """
        processor = CommitResourceProcessor(self.project_id)
        return processor.run(commits, event_candidates)

    def create_model(self, resources: List[Resource]) -> ProvDocument:
        """
        Return PROV document containing commit resource model populated
        with PROV-DM groupings.
        """
        model = CommitResourceModel(self.project_id)

        for resource in resources:
            model.push(resource)

        return model.document()


@dataclass
class IssueResourcePipeline:
    """
    Pipeline that fetches, processes and models project issues.
    """
    project_id: str
    api_client: GitLabProjectWrapper

    async def fetch(self) -> Tuple[List[Issue], ParseableContainer]:
        """
        Retrieve issues, their labels, their awards, their notes and
        the awards of all notes from the project API wrapper.
        """
        async with self.api_client as client:
            issues = await client.issues()
            labels = await client.issue_labels()
            awards = await client.issue_awards()
            notes = await client.issue_notes()
            note_awards = await client.issue_note_awards()

        return issues, ParseableContainer(labels, awards, notes, note_awards)

    def process(self, issues: List[Issue], event_candidates: ParseableContainer) -> List[Resource]:
        """
        Return list of PROV-DM groupings.

        Precompute id's, activities, entities, agents and labels.
        """
        processor = IssueResourceProcessor(self.project_id)
        return processor.run(issues, event_candidates)

    def create_model(self, resources: List[Resource]) -> ProvDocument:
        """
        Return PROV document containing the issue resource model
        populated with PROV-DM groupings.
        """
        model = ResourceModel(self.project_id)

        for resource in resources:
            model.push(resource)

        return model.document()


@dataclass
class MergeRequestResourcePipeline:
    """
    Pipeline that fetches, processes and models project merge requests.
    """

    project_id: str
    api_client: GitLabProjectWrapper

    async def fetch(self) -> Tuple[List[MergeRequest], ParseableContainer]:
        """
        Retrieve merge requests, their labels, their awards, their
        notes and all awards for each note from the project API wrapper.
        """
        async with self.api_client as client:
            merge_requests = await client.merge_requests()
            labels = await client.merge_request_labels()
            awards = await client.merge_request_awards()
            notes = await client.merge_request_notes()
            note_awards = await client.merge_request_note_awards()

        return merge_requests, ParseableContainer(labels, awards, notes, note_awards)

    def process(self, merge_requests: List[MergeRequest], event_candidates: ParseableContainer) -> List[Resource]:
        """
        Return list of PROV-DM groupings.

        Precompute id's, activities, entities, agents and labels.
        """
        processor = MergeRequestResourceProcessor(self.project_id)
        return processor.run(merge_requests, event_candidates)

    def create_model(self, resources: List[Resource]) -> ProvDocument:
        """
        Return PROV document containing the merge request resource model
        populated with PROV-DM groupings.
        """
        model = ResourceModel(self.project_id)

        for resource in resources:
            model.push(resource)

        return model.document()
