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



from copy import deepcopy
from dataclasses import InitVar, asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from gl2p.commons import File, FileStatus
from gl2p.eventparser import EventParser
from gl2p.helpers import by_date, ptime, qname
from gl2p.objects import *
from gl2p.register import FileNameRegister
from prov.constants import PROV_LABEL, PROV_ROLE, PROV_TYPE


@dataclass
class CommitProcessor:
    """
    Turn GitLab Commit and Diff API Resources into PROV vocabulary.
    """

    project_id: str
    file_register: Optional[FileNameRegister] = None
    commit_lookup: Optional[Dict[str, Any]] = None

    def run(self, commits: List[Dict[str, Any]], diffs: List[Any]) -> List[Commit]:
        """
        Return list of objects.Commit ready to insert into model. 

        Precompute labels and id's.
        """
        self.file_register = FileNameRegister(commits, diffs)
        self.commit_lookup = {c.get('id'): c for c in commits}

        processed = []

        for c, df in zip(commits, diffs):
            author = self.author(c)
            committer = self.committer(c)
            commit = self.commit_activity(c)
            parents = self.parent_activities(c)
            files = self.file_changes(c, df)

            processed.append(Commit(author, committer, commit, parents, files))

        return processed

    def author(self, c: Dict[str, Any]) -> PROVNode:
        """
        Returns author of commit *c* as PROVNode.
        """
        id_ = qname(f"user-{c.get('author_name')}")
        label = {
            PROV_TYPE: "user", 
            PROV_ROLE: "author",
            "name": c.get("author_name")
        } 
        return PROVNode(id_, label)

    def committer(self, c: Dict[str, Any]) -> PROVNode:
        """
        Returns committer of commit *c* as PROVNode.
        """
        id_ = qname(f"user-{c.get('committer_name')}")
        label = {
            PROV_TYPE: "user", 
            PROV_ROLE: "committer",
            "name": c.get('committer_name')
        }
        return PROVNode(id_, label)

    def commit_activity(self, c: Dict[str, Any]) -> PROVActivity:
        """
        Returns commit *c* as PROVActivity.
        """
        id_ = qname(f"commit-{c.get('id')}")
        start = ptime(c.get("authored_date"))
        end = ptime(c.get("committed_date"))
        label = {
            PROV_TYPE: "commit", 
            "sha": c.get("id"), 
            "title": c.get("title"), 
            "message": c.get("message")
        }
        return PROVActivity(id_, start, end, label)

    def parent_activities(self, c: Dict[str, Any]) -> List[PROVActivity]:
        """
        Returns list of parent PROVActivities of commit *c*.
        """
        parents = []

        for parent in c.get("parent_ids"):
            parent = self.commit_lookup.get(parent)
            id_ = qname(f"commit-{parent.get('id')}")

            start = ptime(parent.get("authored_date"))
            end = ptime(parent.get("committed_date"))

            label = {
                PROV_TYPE: "commit",
                "sha": parent.get("id"),
                "title": parent.get("title"),
                "message": parent.get("message")
            }
            parents.append(PROVActivity(id_, start, end, label))

        return parents

    def file_changes(self, c: Dict[str, Any], df: List[Dict[str, Any]]) -> List[Union[Addition, Deletion, Modification]]:
        """
        Returns list of file changes. 

        Addition, Modification or Deletion parsed from entries of commit diff *df* of commit *c*.
        """
        files = []

        for entry in df:
            parsed = File.from_diff(entry)
            original = self.file_register.get(c.get("id"), parsed.new_path)

            if parsed.status == FileStatus.ADDED:
                id_ = qname(f"file-{original}")
                label = {
                    PROV_TYPE: "file", 
                    "old_path": parsed.old_path, 
                    "new_path": parsed.new_path
                }
                f = PROVNode(id_, label)
                    
                id_ = qname("file-version-{original}-{c.get('id')}")
                label = {
                    PROV_TYPE: "file_version", 
                    "new_path": parsed.new_path, 
                    "old_path": parsed.old_path
                }
                fv = PROVNode(id_, label)
                files.append(Addition(f, fv))

            elif parsed.status == FileStatus.DELETED:
                id_ = qname(f"file-{original}")
                label = {PROV_TYPE: "file"}
                f = PROVNode(id_, label)
                    
                id_ = qname(f"file-version-{original}-{c.get('id')}")
                label = {
                    PROV_TYPE: "file_version", 
                    "new_path": parsed.new_path, 
                    "old_path": parsed.old_path
                }
                fv = PROVNode(id_, label)
                files.append(Deletion(f, fv))

            elif parsed.status == FileStatus.MODIFIED:
                id_ = qname(f"file-{original}")
                label = {PROV_TYPE: "file"}
                f = PROVNode(id_, label)
                
                id_ = qname(f"file-version-{original}-{c.get('id')}")
                label = {
                    PROV_TYPE: "file_version", 
                    "new_path": parsed.new_path, 
                    "old_path": parsed.old_path
                }
                fv = PROVNode(id_, label)
                
                label = {PROV_TYPE: "file_version"}
                fv_1s = [
                    PROVNode(qname(f"file-version-{original}-{pid}"), label) 
                    for pid in c.get("parent_ids")
                ]
                files.append(Modification(f, fv, fv_1s))

        return files


@dataclass
class CommitResourceProcessor:

    project_id: str

    def run(self, commits: List[Dict[str, Any]], notes: List[List[Dict[str, Any]]]) -> List[Resource]:
        """
        Return list of Resources ready to insert into model.

        Precompute labels and id's.
        """
        processed = []

        for c, nts in zip(commits, notes):
            committer = self.committer(c)
            commit = self.commit_activity(c)
            rcreation = self.commit_creation(c)
            r, rv = self.resource(c)
            events = self.events(c, nts, rcreation, r, rv)

            creation = CommitResourceCreation(committer, commit, rcreation, r, rv)
            processed.append(Resource(creation, events))
        return processed

    def committer(self, c: Dict[str, Any]) -> PROVNode:
        """
        Return committer of commit *c* as PROVNode.
        """
        id_ = qname(f"user-{c.get('committer_name')}")
        label = {
            PROV_TYPE: "user", 
            PROV_ROLE: "event_initiator",
            "name": c.get("committer_name")
        }
        return PROVNode(id_, label)

    def commit_activity(self, c: Dict[str, Any]) -> PROVActivity:
        """
        Returns commit *c* activity as PROVNode.
        """
        id_ = qname(f"commit-{c.get('id')}")
        start = ptime(c.get('authored_date'))
        end = ptime(c.get('committed_date'))
        label = {
            PROV_TYPE: "commit", 
            "sha": c.get('id'),
            "title": c.get('title'),
            "message": c.get("message")
        }
        return PROVActivity(id_, start, end, label)

    def commit_creation(self, c: Dict[str, Any]) -> PROVActivity:
        """
        Returns creation activity of commit *c* as PROVActivity.
        """
        id_ = qname(f"commit-resource-creation-{c.get('id')}")
        start = ptime(c.get("committed_date"))
        end = ptime(c.get("committed_date"))
        label = {PROV_TYPE: "commit_resource_creation"}
        return PROVActivity(id_, start, end, label)
        
    def resource(self, c: Dict[str, Any]) -> Tuple[PROVNode, PROVNode]:
        """
        Return tuple of resource, resource version for resource creation of commit *c*.
        """
        id_ = qname(f"commit-resource-{c.get('id')}")
        label = {PROV_TYPE: "commit_resource"}
        r = PROVNode(id_, label)
            
        id_ = qname(f"commit-resource-{c.get('id')}-original")
        label = {PROV_TYPE: "commit_resource_version"}
        rv = PROVNode(id_, label)

        return r, rv

    def events(self, c: Dict[str, Any], notes: List[Dict[str, Any]], eprev: PROVActivity, r:PROVNode,  rv_1: PROVNode) -> List[Event]:
        """
        Returns list of events that occur on commit *c* ordered by creation date asc.
        """
        events = []
        notes = sorted(notes, key=by_date)

        for note in notes:
            parsed = EventParser.parse_note(note)
            
            id_ = qname(f"user-{parsed.initiator}")
            label = {PROV_TYPE: "user", "name": parsed.initiator}
            initiator = PROVNode(id_, label)
            
            id_ = qname(f"commit-resource-event-{parsed.identifier}")
            start = ptime(parsed.created_at)
            end = ptime(parsed.created_at)
            label = {PROV_TYPE: "commit_event", "event_type": parsed.type}
            event = PROVActivity(id_, start, end, label)
            
            id_ = qname(f"{r.id}-version-{parsed.identifier}")
            label = {PROV_TYPE: "commit_resource_version"}
            rv = PROVNode(id_, label)

            events.append(Event(initiator, event, eprev, r, rv, rv_1))

            # update last event, last resource
            eprev = event
            rv_1 = rv

        return events
