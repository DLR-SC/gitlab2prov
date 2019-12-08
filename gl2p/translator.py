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
            c = commit.attributes.get("id")
            f, fv = unique_id("ORIGINAL", nametables.get(c).get(fil.new_path)), unique_id(c, fil.new_path)
            author = unique_id(commit.attributes.get("author_name"))
            committer = unique_id(commit.attributes.get("committer_name"))

            if fil.status == FileStatus.ADDED:
                # Nodes
                document.entity(f)
                document.entity(fv)
                document.agent(author) 
                document.agent(committer)
                document.activity(c)
                for parent in commit.attributes.get("parent_ids"):
                    document.activity(parent)
                # Relations
                if fv not in specialized:
                    document.specializationOf(fv, f) # id: version
                    specialized.add(fv)
                document.wasAttributedTo(fv, author)
                document.wasAttributedTo(f, author)
                document.wasAssociatedWith(c, author)
                document.wasAssociatedWith(c, committer)
                document.wasGeneratedBy(f, c)
                document.wasGeneratedBy(fv, c)
                for parent in commit.attributes.get("parent_ids"):
                    document.wasInformedBy(c, parent, identifier=c+parent)

            if fil.status == FileStatus.MODIFIED:
                # Nodes
                document.entity(fv)
                document.agent(author)
                document.agent(committer)
                document.activity(c)
                for parent in commit.attributes.get("parent_ids"):
                    fv_prev = unique_id(parent, fil.old_path)
                    document.activity(parent)
                    document.entity(fv_prev)
                
                # Relations
                if fv not in specialized:
                    document.specializationOf(fv, f)
                    specialized.add(fv)
                document.wasGeneratedBy(fv, c)
                document.wasAssociatedWith(c, author)
                document.wasAssociatedWith(c, committer)
                document.wasAttributedTo(fv, author)
                for parent in commit.attributes.get("parent_ids"):
                    fv_prev = unique_id(parent, fil.old_path)
                    fv_prev_original = unique_id("ORIGINAL", nametables.get(parent).get(fil.old_path))
                    document.entity(fv_prev_original)
                    document.used(c, fv_prev)
                    document.wasDerivedFrom(fv, fv_prev)
                    if fv_prev not in specialized:
                        document.specializationOf(fv_prev, fv_prev_original)
                        specialized.add(fv_prev)
                    document.wasInformedBy(c, parent, identifier=c+parent)

            if fil.status == FileStatus.DELETED:
                # Nodes
                document.activity(c)
                document.agent(author)
                document.agent(committer)
                for parent in commit.attributes.get("parent_ids"):
                    fv_prev = unique_id(parent, fil.old_path)
                    document.entity(fv_prev)
                    document.activity(parent)

                # Relations
                document.wasAssociatedWith(c, author)
                document.wasAssociatedWith(c, committer)
                for parent in commit.attributes.get("parent_ids"):
                    fv_prev = unique_id(parent, fil.old_path)
                    fv_prev_original = unique_id("ORIGINAL", nametables.get(parent).get(fil.old_path))
                    document.entity(fv_prev_original)
                    if fv_prev not in specialized:
                        document.specializationOf(fv_prev, fv_prev_original)
                        specialized.add(fv_prev)
                    document.wasInformedBy(c, parent, identifier=c+parent)
                    document.wasInvalidatedBy(fv_prev, c)
        
        # Commit Entity Model

        document = document.unified()
        return document
