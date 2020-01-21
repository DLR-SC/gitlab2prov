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


from dataclasses import dataclass, field, InitVar, asdict
from typing import List, Any, Dict, Iterable, Union
from copy import deepcopy
from prov.constants import PROV_TYPE, PROV_ROLE, PROV_LABEL

from gl2p.eventparser import EventParser
from gl2p.register import FileNameRegister
from gl2p.commons import File, FileStatus
from gl2p.helpers import qname, by_date, parse_time
from gl2p.objects import *


@dataclass
class CommitProcessor:

    project_id: str

    def run(self, commits, diffs):

        self.filenameregister = FileNameRegister(commits, diffs)

        commit_lookup = {c.get('id'): c for c in commits}

        processed = []

        for c, diff in zip(commits, diffs):
                
            author_id = f"user-{c.get('author_name')}"
            author_label = {PROV_TYPE: "user", "name": c.get("author_name")}
            author = PROVNode(author_id, author_label)

            committer_id = f"user-{c.get('committer_name')}"
            committer_label = {PROV_TYPE: "user", "name": c.get('committer_name')}
            committer = PROVNode(committer_id, labels=committer_label)
            
            commit_id = f"commit-{c.get('id')}"
            commit_label = {
                PROV_TYPE: "commit", 
                "sha": c.get('id'), 
                "title": c.get('title'), 
                "message": " ".join(c.get("message").split("\n"))
            }
            commit_start = parse_time(c.get("authored_date"))
            commit_end = parse_time(c.get("committed_date"))
            commit = PROVActivity(commit_id, labels=commit_label, start=commit_start, end=commit_end)

            parent_commits = []
            for parent in (commit_lookup.get(pid) for pid in c.get("parent_ids")):
                parent_commit_id = f"commit-{parent.get('id')}"
                parent_commit_label = {
                    PROV_TYPE: "commit",
                    "sha": parent.get('id'),
                    "title": parent.get('title'),
                    "message": " ".join(parent.get("message").split("\n"))
                }
                parent_commit_start = parse_time(parent.get("authored_date"))
                parent_commit_end = parse_time(parent.get("committed_date"))
                parent_commits.append(
                    PROVActivity(parent_commit_id, labels=parent_commit_label, start=parent_commit_start, end=parent_commit_end)
                )
            
            files = []
            for entry in diff:
                f = File.from_diff(entry)

                original = self.filenameregister.get(c.get("id"), f.new_path)

                if f.status == FileStatus.ADDED:
                    file_label = {
                        PROV_TYPE: "file", 
                        "old_path": f.old_path, 
                        "new_path": f.new_path
                    }
                    file_ = PROVNode(f"file-{original}", labels=file_label)

                    file_v_label = {
                        PROV_TYPE: "file_version", 
                        "new_path": f.new_path, 
                        "old_path": f.old_path
                    }
                    file_v = PROVNode(f"file-version-{original}-{c.get('id')}", labels=file_v_label)

                    f = Addition(file_, file_v)

                elif f.status == FileStatus.DELETED:
                    file_label = {PROV_TYPE: "file"}
                    file_ = PROVNode(f"file-{original}", labels=file_label)

                    file_v_label = {
                        PROV_TYPE: "file_version", 
                        "new_path": f.new_path, 
                        "old_path": f.old_path
                    }
                    file_v = PROVNode(f"file-version-{original}-{c.get('id')}", labels=file_v_label)

                    f = Deletion(file_, file_v)

                elif f.status == FileStatus.MODIFIED:
                    file_label = {PROV_TYPE: "file"}
                    file_ = PROVNode(f"file-{original}", labels=file_label)

                    file_v_label = {
                        PROV_TYPE: "file_version", 
                        "new_path": f.new_path, 
                        "old_path": f.old_path
                    }
                    file_v = PROVNode(f"file-version-{original}-{c.get('id')}", labels=file_v_label)
                    
                    file_v_1_label = {PROV_TYPE: "file_version"}
                    file_v_1 = [PROVNode(f"file-version-{original}-{pid}", labels=file_v_1_label) for pid in c.get("parent_ids")]

                    f = Modification(file_, file_v, file_v_1)

                files.append(f)
            
            processed.append(Commit(author, parent_commits, committer, commit, files))

        return processed

@dataclass
class CommitResourceProcessor:

    project_id: str

    def run(self, commits, notes):

        processed = []

        for c, notes in zip(commits, notes):

            committer_label = {
                PROV_TYPE: "user", 
                "name": c.get("committer_name")
            }
            committer = PROVNode(f"user-{c.get('committer_name')}", labels=committer_label)
            
            commit_label = {
                PROV_TYPE: "commit", 
                "sha": c.get('id'),
                "title": c.get('title'),
                "message": " ".join(c.get("message").split("\n"))
            }
            commit = PROVActivity(f"commit-{c.get('id')}", start=parse_time(c.get('authored_date')), end=parse_time(c.get("committed_date")), labels=commit_label)

            resource_creation_label = {PROV_TYPE: "commit_resource_creation"}
            resource_creation = PROVActivity(f"commit-resource-creation-{c.get('id')}", labels=resource_creation_label, start=parse_time(c.get("committed_date")), end=parse_time(c.get("commited_date")))

            resource_label = {PROV_TYPE: "commit_resource"}
            resource = PROVNode( f"commit-resource-{c.get('id')}", labels=resource_label)

            resource_v_label = {PROV_TYPE: "commit_resource_version"}
            resource_v = PROVNode( f"commit-resource-{c.get('id')}-original", labels=resource_v_label)

            creation = CommitResourceCreation(committer, commit, resource_creation, resource, resource_v)

            previous_event = resource_creation
            resource_v_1 = resource_v

            notes = sorted(notes, key=by_date)
            events = []

            for note in notes:
                parsed_event = EventParser.parse_note(note)
                
                initiator_label = {PROV_TYPE: "user", "name": parsed_event.initiator}
                initiator = PROVNode(f"user-{parsed_event.initiator}", labels=initiator_label)

                event_label = {PROV_TYPE: "commit_event", "event_type": parsed_event.type}
                event = PROVActivity(f"commit-resource-event-{parsed_event.identifier}", labels={PROV_TYPE: "resource_event", "type": parsed_event.type}, start=parsed_event.created_at, end=parsed_event.created_at)

                resource_v_label = {PROV_TYPE: "commit_resource_version"}
                resource_v = PROVNode(f"{resource.identifier}-version-{parsed_event.identifier}", labels=resource_v_label)

                events.append(Event(initiator, event, previous_event, resource, resource_v, resource_v_1))

                # update last event, last resource
                previous_event = event
                resource_v_1 = resource_v

            processed.append(Resource(creation, events))

        return processed
