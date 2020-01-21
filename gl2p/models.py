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


from prov.model import ProvDocument
from dataclasses import dataclass, InitVar, field
from typing import Set
from gl2p.helpers import qname
from gl2p.helpers import parse_time as date
from gl2p.commons import FileStatus
from gl2p.objects import PROVNode, Event, CommitResourceCreation, Addition, Modification, Deletion, Resource


@dataclass 
class Model:

    project_id: InitVar[str]
    doc: ProvDocument = ProvDocument()

    def __post_init__(self, project_id):
        
        self.doc = ProvDocument()
        self.doc.set_default_namespace("gl2p:")
        self.pb = self.doc.bundle(project_id.replace("%2F", "-"))

    def document(self):
        """Return self.doc."""

        return self.doc


@dataclass
class Commit(Model):

    unique_check: Set = field(default_factory=set)

    def push(self, commit):
        """Populate git commit model."""

        author = commit.author
        committer = commit.committer
        parents = commit.parent_commits
        files = commit.files
        commit = commit.commit

        self.pb.agent(author.identifier, other_attributes=author.labels)
        self.pb.agent(committer.identifier, other_attributes=committer.labels)
        self.pb.activity(commit.identifier, commit.start, commit.end, other_attributes=commit.labels)

        self.pb.wasAssociatedWith(commit.identifier, committer.identifier)
        self.pb.wasAssociatedWith(commit.identifier, author.identifier)
    
        for parent_commit in parents:
            self.pb.activity(parent_commit.identifier, parent_commit.start, parent_commit.end, other_attributes=parent_commit.labels)
            self.pb.wasInformedBy(commit.identifier, parent_commit.identifier)

        for f in files:

            if isinstance(f, Addition):
                self.pb.entity(f.file.identifier, other_attributes=f.file.labels)
                self.pb.entity(f.file_v.identifier, other_attributes=f.file_v.labels)
                self.pb.wasGeneratedBy(f.file.identifier, commit.identifier)
                self.pb.wasGeneratedBy(f.file_v.identifier, commit.identifier)
                self.pb.wasAttributedTo(f.file.identifier, author.identifier)
                self.pb.wasAttributedTo(f.file_v.identifier, author.identifier)
                self.specializationOf(f.file_v.identifier, f.file.identifier)

            elif isinstance(f, Modification):
                self.pb.entity(f.file.identifier, other_attributes=f.file.labels)
                self.pb.entity(f.file_v.identifier, other_attributes=f.file_v.labels)
                self.pb.wasAttributedTo(f.file_v.identifier, author.identifier)
                self.pb.wasGeneratedBy(f.file_v.identifier, commit.identifier)
                self.specializationOf(f.file_v.identifier, f.file.identifier)

                for f_v_1 in f.file_v_1:
                    self.pb.entity(f_v_1.identifier, other_attributes=f_v_1.labels)
                    self.pb.used(commit.identifier, f_v_1.identifier)
                    self.pb.wasDerivedFrom(f.file_v.identifier, f_v_1.identifier)
                    self.specializationOf(f_v_1.identifier, f.file.identifier)

            elif isinstance(f, Deletion):
                self.pb.entity(f.file.identifier, other_attributes=f.file.labels)
                self.pb.entity(f.file_v.identifier, other_attributes=f.file_v.labels)
                self.specializationOf(f.file_v.identifier, f.file.identifier)
                self.pb.wasInvalidatedBy(f.file_v.identifier, commit.identifier)

        return 

    def specializationOf(self, entity, general_entity):
        """Only allow one specializationOf relation per entity."""

        if (entity, general_entity) in self.unique_check:
            return

        self.pb.specializationOf(entity, general_entity)
        self.unique_check.add((entity, general_entity))


@dataclass
class CommitResource(Model):

    def push(self, resource: PROVNode):

        creation = resource.creation # type: CommitResourceCreation
        events = resource.events  # type: List[ResourceEvent]

        committer = self.pb.agent(creation.committer.identifier, other_attributes=creation.committer.labels)
        commit = self.pb.activity(creation.commit.identifier, creation.commit.start, creation.commit.end, other_attributes=creation.commit.labels)
        resource_creation = self.pb.activity(creation.resource_creation.identifier, creation.resource_creation.start, creation.resource_creation.end, other_attributes=creation.resource_creation.labels)
        resource = self.pb.entity(creation.resource.identifier, other_attributes=creation.resource.labels)
        resource_v = self.pb.entity(creation.resource_v.identifier, other_attributes=creation.resource_v.labels)

        self.pb.wasAssociatedWith(commit, committer)
        self.pb.wasAssociatedWith(resource_creation, committer)
        self.pb.wasAttributedTo(resource, committer)
        self.pb.wasInformedBy(resource_creation, commit)
        self.pb.wasAttributedTo(resource_v, committer)
        self.pb.wasGeneratedBy(resource, resource_creation)
        self.pb.wasGeneratedBy(resource_v, resource_creation)
        self.pb.specializationOf(resource_v, resource)

        for e in events:
            resource = self.pb.entity(e.resource.identifier, other_attributes=e.resource.labels)
            resource_v_1 = self.pb.entity(e.resource_v_1.identifier, other_attributes=e.resource_v_1.labels)
            previous_event = self.pb.activity(e.previous_event.identifier, other_attributes=e.previous_event.labels)
            initiator = self.pb.agent(e.initiator.identifier, other_attributes=e.initiator.labels)
            event = self.pb.activity(e.event.identifier, e.event.start, e.event.end, other_attributes=e.event.labels)
            resource_v = self.pb.entity(e.resource_v.identifier, other_attributes=e.resource_v.labels)

            self.pb.specializationOf(resource_v, resource)
            self.pb.used(event, resource_v_1)
            self.pb.wasInformedBy(event, previous_event)
            self.pb.wasAssociatedWith(event, initiator)
            self.pb.wasDerivedFrom(resource_v, resource_v_1)
            self.pb.wasAttributedTo(resource_v, initiator)
            self.pb.wasGeneratedBy(resource_v, event)


@dataclass
class IssueResource(Model):

    def push(self, resource: Resource):

        creation = resource.creation
        events = resource.events

        creator = self.pb.agent(creation.creator.identifier, other_attributes=creation.creator.labels)
        resource_creation = self.pb.activity(creation.resource_creation.identifier, creation.resource_creation.start, creation.resource_creation.end, other_attributes=creation.resource_creation.labels)
        resource = self.pb.entity(creation.resource.identifier, other_attributes=creation.resource.labels)
        resource_v = self.pb.entity(creation.resource_v.identifier, other_attributes=creation.resource_v.labels)


        self.pb.wasAssociatedWith(resource_creation, creator)
        self.pb.wasAttributedTo(resource, creator)
        self.pb.wasAttributedTo(resource_v, creator)
        self.pb.wasGeneratedBy(resource, resource_creation)
        self.pb.wasGeneratedBy(resource_v, resource_creation)
        self.pb.specializationOf(resource_v, resource)

        for e in events:
            resource = self.pb.entity(e.resource.identifier, other_attributes=e.resource.labels)
            resource_v = self.pb.entity(e.resource_v.identifier, other_attributes=e.resource_v.labels)
            resource_v_1 = self.pb.entity(e.resource_v_1.identifier, other_attributes=e.resource_v_1.labels)
            previous_event = self.pb.activity(e.previous_event.identifier, other_attributes=e.previous_event.labels)
            event = self.pb.activity(e.event.identifier, e.event.start, e.event.end, other_attributes=e.event.labels)
            initiator = self.pb.agent(e.initiator.identifier, other_attributes=e.initiator.labels)

            self.pb.specializationOf(resource_v, resource)
            self.pb.used(event, resource_v_1)
            self.pb.wasDerivedFrom(resource_v, resource_v_1)
            self.pb.wasGeneratedBy(resource_v, event)
            self.pb.wasInformedBy(event, previous_event)
            self.pb.wasAssociatedWith(event, initiator)
            self.pb.wasAttributedTo(resource_v, initiator)


@dataclass
class MergeRequestResource(Model):

    def push(self, resource: Resource):

        creation = resource.creation
        events = resource.events

        creator = self.pb.agent(creation.creator.identifier, other_attributes=creation.creator.labels)
        resource_creation = self.pb.activity(creation.resource_creation.identifier, creation.resource_creation.start, creation.resource_creation.end, other_attributes=creation.resource_creation.labels)
        resource = self.pb.entity(creation.resource.identifier, other_attributes=creation.resource.labels)
        resource_v = self.pb.entity(creation.resource_v.identifier, other_attributes=creation.resource_v.labels)

        self.pb.wasAssociatedWith(resource_creation, creator)
        self.pb.wasAttributedTo(resource, creator)
        self.pb.wasAttributedTo(resource_v, creator)
        self.pb.wasGeneratedBy(resource, resource_creation)
        self.pb.wasGeneratedBy(resource_v, resource_creation)
        self.pb.specializationOf(resource_v, resource)

        for e in events:
            resource = self.pb.entity(e.resource.identifier, other_attributes=e.resource.labels)
            resource_v = self.pb.entity(e.resource_v.identifier, other_attributes=e.resource_v.labels)
            resource_v_1 = self.pb.entity(e.resource_v_1.identifier, other_attributes=e.resource_v_1.labels)
            previous_event = self.pb.activity(e.previous_event.identifier, other_attributes=e.previous_event.labels)
            event = self.pb.activity(e.event.identifier, e.event.start, e.event.end, other_attributes=e.event.labels)
            initiator = self.pb.agent(e.initiator.identifier, other_attributes=e.initiator.labels)

            self.pb.specializationOf(resource_v, resource)
            self.pb.used(event, resource_v_1)
            self.pb.wasDerivedFrom(resource_v, resource_v_1)
            self.pb.wasGeneratedBy(resource_v, event)
            self.pb.wasInformedBy(event, previous_event)
            self.pb.wasAssociatedWith(event, initiator)
            self.pb.wasAttributedTo(resource_v, initiator)
