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


from dataclasses import InitVar, dataclass, field
from typing import Any, Optional, Set

from gl2p.commons import FileStatus
#from gl2p.helpers import parse_time as date
from gl2p.helpers import qname
from gl2p.objects import *
from gl2p.objects import (Addition, CommitResourceCreation, Deletion, Event,
                          Modification, PROVNode, Resource)
from prov.model import ProvBundle, ProvDocument


@dataclass
class Model:
    """
    Model implementation base class for models in ../models.
    """
    project_id: InitVar[str]
    doc: Optional[ProvDocument] = None
    bundle: Optional[ProvBundle] = None

    def __post_init__(self, project_id: str):
        self.project_id = project_id.replace("%2F", "-")
        self.doc = ProvDocument()
        self.doc.set_default_namespace("gl2p:")
        self.bundle = self.doc.bundle(self.project_id)

    def push(self, resource: Any):
        raise NotImplementedError

    def document(self) -> ProvDocument:
        return self.doc


@dataclass
class Commit(Model):
    """
    Model implementation for commit model.
    """
    relation_store: Set = field(default_factory=set)

    def push(self, resource: Commit) -> None:
        """
        Push resource into model document.
        """
        bundle = self.bundle
        author, committer, commit, parents, files = resource

        bundle.agent(*author)
        bundle.agent(*committer)
        bundle.activity(*commit)
        bundle.wasAssociatedWith(commit.id, author.id)
        bundle.wasAssociatedWith(commit.id, committer.id)

        for parent in parents:
            bundle.activity(*parent)
            bundle.wasInformedBy(commit.id, parent.id)

        for f in files:
            if isinstance(f, Addition):
                f, fv = f
                bundle.entity(*f)
                bundle.entity(*fv)
                bundle.wasGeneratedBy(f.id, commit.id)
                bundle.wasGeneratedBy(fv.id, commit.id)
                bundle.wasAttributedTo(f.id, author.id)
                bundle.wasAttributedTo(fv.id, author.id)
                if self.unique_specialization_of(fv.id, f.id):
                    bundle.specializationOf(fv.id, f.id)

            if isinstance(f, Modification):
                f, fv, fv_1s = f
                bundle.entity(*f)
                bundle.entity(*fv)
                bundle.wasAttributedTo(fv.id, commit.id)
                bundle.wasGeneratedBy(fv.id, commit.id)
                if self.unique_specialization_of(fv.id, f.id):
                    bundle.specializationOf(fv.id, f.id)
                for fv_1 in fv_1s:
                    bundle.entity(*fv_1)
                    bundle.used(commit.id, fv_1.id)
                    bundle.wasDerivedFrom(fv.id, fv_1.id)
                    if self.unique_specialization_of(fv_1.id, f.id):
                        bundle.specializationOf(fv_1.id, f.id)

            if isinstance(f, Deletion):
                f, fv = f
                bundle.entity(*f)
                bundle.entity(*fv)

                if self.unique_specialization_of(fv.id, f.id):
                    bundle.specializationOf(fv.id, f.id)
                bundle.wasInvalidatedBy(fv.id, commit.id)
        return

    def unique_specialization_of(self, start: str, target: str) -> bool:
        """
        Return whether nodes *start* and *target* are already related by a specializationOf relation.

        *start* and *target* are id strings representing a node.
        """
        tp = (start, target)
        if tp not in self.relation_store:
            self.relation_store.add(tp)
            return True
        return False


@dataclass
class CommitResource(Model):
    """
    Model implementation for commit resource model.
    """

    def push(self, resource: Resource) -> None:
        """
        Push resource into model document.
        """
        bundle = self.bundle

        # creation 
        creation, _ = resource

        committer, commit, rcreation, r, rv = creation

        bundle.activity(*commit)
        bundle.activity(*rcreation)
        bundle.agent(*committer)
        bundle.entity(*r)
        bundle.entity(*rv)

        bundle.wasAssociatedWith(commit.id, committer.id)
        bundle.wasAssociatedWith(rcreation.id, committer.id)
        bundle.wasAttributedTo(r.id, committer.id)
        bundle.wasInformedBy(rcreation.id, commit.id)
        bundle.wasAttributedTo(rv.id, committer.id)
        bundle.wasGeneratedBy(r.id, rcreation.id)
        bundle.wasGeneratedBy(rv.id, rcreation.id)
        bundle.specializationOf(rv.id, r.id)
        
        # event chain
        _, events = resource

        for event in events:
            user, e, eprev, r, rv, rv_1 = event

            bundle.entity(*r)
            bundle.entity(*rv)
            bundle.entity(*rv_1)
            bundle.activity(*e)
            bundle.activity(*eprev)
            bundle.agent(*user)

            bundle.specializationOf(rv.id, r.id)
            bundle.used(e.id, rv_1.id)
            bundle.wasInformedBy(e.id, eprev.id)
            bundle.wasAssociatedWith(e.id, user.id)
            bundle.wasDerivedFrom(rv.id, rv_1.id)
            bundle.wasAttributedTo(rv.id, user.id)
            bundle.wasGeneratedBy(rv.id, e.id)
        return
