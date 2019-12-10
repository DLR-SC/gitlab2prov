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


from collections import defaultdict, deque
from prov.model import ProvDocument, ProvSpecialization
from prov.constants import PROV_LABEL, PROV_ROLE, PROV_TYPE
from gl2p.helpers import unique_id
from gl2p.commons import FileStatus


# NODE TYPES
# USED TO DISTINGUISH ID NAMESPACES
FILE_ORIGINAL = "FILE_ORIGINAL"
FILE_VERSION = "FILE_VERSION"
COMMIT_ENTITY = "COMMIT_ENTITY"
COMMIT_VERSION = "COMMIT_VERSION"
COMMIT_ACTIVITY = "COMMIT_ACTIVITY"
COMMIT_EVENT = "COMMIT_EVENT"
ISSUE_EVENT = "ISSUE_EVENT"
ISSUE_ENTITY = "ISSUE_ENTITY"
ISSUE_VERSION = "ISSUE_VERSION"
MERGE_REQUEST_ENTITY = "MERGE_REQUEST_ENTITY"
MERGE_REQUEST_EVENT = "MERGE_REQUEST_EVENT"
MERGE_REQUEST_VERSION = "MERGE_REQUEST_VERSION"
USER = "USER"


class Translator:

    def __init__(self):
        pass

    def run(self, repository):
        document = ProvDocument()
        document.set_default_namespace("gl2p:")

        commits = repository.commits
        nametables = repository.nametables
        specialized = set()

        for commit, fil in ((c, f) for c in commits for f in c.attributes.get("files")):
            sha = commit.attributes.get("id")
            c = unique_id([sha], prefix=COMMIT_ACTIVITY)
            f = unique_id([nametables.get(sha).get(fil.new_path)], prefix=FILE_ORIGINAL)
            fv = unique_id([c, fil.new_path], prefix=FILE_VERSION)
            author = unique_id([commit.attributes.get("author_name")], prefix=USER)
            committer = unique_id([commit.attributes.get("committer_name")], prefix=USER)

            if fil.status == FileStatus.ADDED:
                # Nodes
                document.entity(f)
                document.entity(fv)
                document.agent(author) 
                document.agent(committer)
                document.activity(c)
                for parent in commit.attributes.get("parent_ids"):
                    parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                    document.activity(parent)
                # Relations
                document.wasAttributedTo(fv, author)
                document.wasAttributedTo(f, author)
                document.wasAssociatedWith(c, author)
                document.wasAssociatedWith(c, committer)
                document.wasGeneratedBy(f, c)
                document.wasGeneratedBy(fv, c)
                if fv not in specialized:
                    document.specializationOf(fv, f) # id: version
                    specialized.add(fv)
                for parent in commit.attributes.get("parent_ids"):
                    parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                    document.wasInformedBy(c, parent, identifier=c+parent)

            if fil.status == FileStatus.MODIFIED:
                # Nodes
                document.entity(fv)
                document.agent(author)
                document.agent(committer)
                document.activity(c)
                for parent in commit.attributes.get("parent_ids"):
                    parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                    fv_prev = unique_id([parent, fil.old_path], prefix=FILE_VERSION)
                    document.activity(parent)
                    document.entity(fv_prev)
                
                # Relations
                document.wasGeneratedBy(fv, c)
                document.wasAssociatedWith(c, author)
                document.wasAssociatedWith(c, committer)
                document.wasAttributedTo(fv, author)
                if fv not in specialized:
                    document.specializationOf(fv, f)
                    specialized.add(fv)
                for parent in commit.attributes.get("parent_ids"):
                    prev_original = nametables.get(parent).get(fil.old_path)
                    parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                    fv_prev = unique_id([parent, fil.old_path], prefix=FILE_VERSION)
                    fv_prev_original = unique_id([prev_original], prefix=FILE_ORIGINAL)
                    document.entity(fv_prev_original)
                    document.used(c, fv_prev)
                    document.wasDerivedFrom(fv, fv_prev)
                    document.wasInformedBy(c, parent, identifier=c+parent)
                    if fv_prev not in specialized:
                        document.specializationOf(fv_prev, fv_prev_original)
                        specialized.add(fv_prev)

            if fil.status == FileStatus.DELETED:
                # Nodes
                document.activity(c)
                document.agent(author)
                document.agent(committer)
                for parent in commit.attributes.get("parent_ids"):
                    parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                    fv_prev = unique_id([parent, fil.old_path], prefix=FILE_VERSION)
                    document.entity(fv_prev)
                    document.activity(parent)

                # Relations
                document.wasAssociatedWith(c, author)
                document.wasAssociatedWith(c, committer)
                for parent in commit.attributes.get("parent_ids"):
                    prev_original = nametables.get(parent).get(fil.old_path)
                    parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                    fv_prev = unique_id([parent, fil.old_path], prefix=FILE_VERSION)
                    fv_prev_original = unique_id([prev_original], prefix=FILE_ORIGINAL)
                    document.entity(fv_prev_original)
                    document.wasInvalidatedBy(fv_prev, c)
                    document.wasInformedBy(c, parent, identifier=c+parent)
                    if fv_prev not in specialized:
                        document.specializationOf(fv_prev, fv_prev_original)
                        specialized.add(fv_prev)


        # Commit Model - New Commit
        for commit in commits:
            ca = unique_id([commit.attributes.get("id")], prefix=COMMIT_ACTIVITY)
            ce = unique_id([ca], prefix=COMMIT_ENTITY)
            cv = unique_id([ca], prefix=COMMIT_VERSION)
            committer = unique_id([commit.attributes.get("committer_name")], prefix=USER)
            # Nodes
            document.entity(ce)
            document.entity(cv)
            document.activity(ca)
            document.agent(committer)
            for parent in commit.attributes.get("parent_ids"):
                parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                document.activity(parent)
            # Relations
            document.wasGeneratedBy(ce, ca)
            document.wasGeneratedBy(cv, ca)
            document.wasAttributedTo(ce, committer)
            document.wasAttributedTo(cv, committer)
            document.wasAssociatedWith(ca, committer)
            if cv not in specialized:
                document.specializationOf(cv, ce)
                specialized.add(cv)
            for parent in commit.attributes.get("parent_ids"):
                parent = unique_id([parent], prefix=COMMIT_ACTIVITY)
                document.wasInformedBy(ca, parent, identifier=ca+parent)


        # Commit Model - New Commit Event
        for commit in commits:
            sha = commit.attributes.get("id")
            ca = unique_id([sha], prefix=COMMIT_ACTIVITY)
            ce = unique_id([ca], prefix=COMMIT_ENTITY)
            cv_prev = unique_id([ca], prefix=COMMIT_VERSION)
            event_prev = ca
            for event in commit.events:
                initiator = unique_id([event.initiator], prefix=USER)
                event = unique_id([event.id], prefix=COMMIT_EVENT)
                cv = unique_id([ca, event], prefix=COMMIT_VERSION)
                # Nodes
                document.entity(ce)
                document.entity(cv)
                document.entity(cv_prev)
                document.activity(event)
                document.agent(initiator)
                # Relations
                document.wasDerivedFrom(cv, cv_prev)
                document.wasGeneratedBy(cv, event)
                document.used(event, cv_prev)
                document.wasAttributedTo(cv, initiator)
                document.wasAssociatedWith(event, initiator)
                document.wasInformedBy(event, event_prev)
                if cv not in specialized:
                    document.specializationOf(cv, ce)
                # Update prev values
                cv_prev = cv
                event_prev = event

        document = document.unified()
        return document
