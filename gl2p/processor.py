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

from typing import List, Optional, Union
from dataclasses import dataclass
from prov.constants import PROV_ROLE, PROV_TYPE
from gl2p.eventparser import EventParser
from gl2p.history import FileNameHistory
from gl2p.utils.objects import (CommitResource, Event, Resource, Creation, Agent,
                                Entity, Activity, CommitCreation, ParseableContainer,
                                Candidates, Addition, Deletion, Modification)
from gl2p.utils.types import Commit, Issue, MergeRequest, Diff
from gl2p.utils.helpers import qname, ptime


def author(project_id: str, commit: Commit) -> Agent:
    """
    Return the author of *commit* as a PROV agent.
    """
    return Agent(
        id=qname(

            f"{project_id}" + f"user-{commit['committer_name']}"

        ),
        label={
            PROV_TYPE: "user",
            PROV_ROLE: "committer",
            "name": commit["committer_name"]
        }
    )


def committer(project_id: str, commit: Commit) -> Agent:
    """
    Return the committer of *commit* as a PROV agent.
    """
    return Agent(
        id=qname(

            f"{project_id}" + f"user-{commit['committer_name']}"

        ),
        label={
            PROV_TYPE: "user",
            PROV_ROLE: "committer",
            "name": commit["committer_name"]
        }
    )


def commit_activity(project_id: str, commit: Commit) -> Activity:
    """
    Return the commit activity denoted by *commit*.
    """
    id_ = qname(f"{project_id}-commit-activity-{commit['id']}")

    start = ptime(commit["authored_date"])
    end = ptime(commit["committed_date"])

    label = {
        PROV_TYPE: "commit",
        "sha": commit["id"],
        "title": commit["title"],
        "message": commit["message"]
    }

    return Activity(id_, start, end, label)


def parents(project_id: str, commit: Commit, all_commits: List[Commit]) -> List[Activity]:
    """
    Return the parent commit activities of *commit*.

    Build a lookup of all commits.
    """
    # TODO: cache the lookup, this is inefficient.
    # NOTE: or outsource it, should be fine.
    clookup = {c["id"]: c for c in all_commits}

    # return list of parenting commit activities
    return [commit_activity(project_id, clookup[pid]) for pid in commit["parent_ids"]]


@dataclass
class CommitProcessor:
    """
    Preprocess commit data before dumping into PROV model.
    """
    project_id: str
    history: FileNameHistory = FileNameHistory()

    def run(self, commits: List[Commit], diffs: List[Diff]) -> List[CommitResource]:
        """
        """
        self.history.compute(commits, diffs)

        processed = []

        for commit, diff in zip(commits, diffs):
            processed.append(
                CommitResource(**{
                    "author": author(self.project_id, commit),
                    "committer": committer(self.project_id, commit),
                    "commit": commit_activity(self.project_id, commit),
                    "parents": parents(self.project_id, commit, commits),
                    "changes": self.changes(commit, diff)
                })
            )
        return processed

    def changes(self, commit: Commit, diff: Diff) -> List[Union[Addition, Deletion, Modification]]:
        """
        Return diff entries parsed as FileChanges.
        """
        changes: List[Union[Addition, Deletion, Modification]] = []

        for entry in diff:

            # get original file name of file denoted in diff entry
            original = self.history.get(commit["id"], entry["new_path"])

            f = Entity(id=qname(f"{self.project_id}-file-{original}"), label={PROV_TYPE: "file"})
            f_version = Entity(
                id=qname(f"{self.project_id}-file-{original}-{commit['id']}"),
                label={
                    PROV_TYPE: "file_version",
                    "old_path": entry["old_path"],
                    "new_path": entry["new_path"]
                }
            )

            if entry["new_file"]:
                changes.append(Addition(f, f_version))

            elif entry["deleted_file"]:
                changes.append(Deletion(f, f_version))

            elif entry["new_path"] != entry["old_path"]:
                previous_f_versions = [
                    Entity(
                        id=qname(f"{self.project_id}-file-{original}-{pid}"),
                        label={PROV_TYPE: "file_version"}
                    )
                    for pid in commit["parent_ids"]
                ]
                changes.append(Modification(f, f_version, previous_f_versions))

        return changes


@dataclass
class CommitResourceProcessor:
    """
    Preprocess commit resource data before handing over to model population.
    """
    project_id: str
    eventparser: EventParser = EventParser()

    def run(self, commits: List[Commit], parsables: ParseableContainer) -> List[Resource]:
        """
        Return list of PROV-DM commit resources.
        """
        processed = []

        for commit, candidates in zip(commits, parsables):

            processed.append(
                Resource(
                    self.creation(commit),
                    self.events(commit, candidates)
                )
            )

        return processed

    def creation(self, commit: Commit) -> CommitCreation:
        """
        Return PROV-DM creation grouping for *commit*.
        """
        return CommitCreation(**{
            "committer": committer(self.project_id, commit),

            "commit": commit_activity(self.project_id, commit),

            "creation": Activity(
                id=qname(f"{self.project_id}-commit-creation-{commit['id']}"),
                start=ptime(commit["committed_date"]),
                end=ptime(commit["committed_date"]),
                label={PROV_TYPE: "commit_creation"}
            ),

            "resource": Entity(
                id=qname(f"{self.project_id}-commit-{commit['id']}"),
                label={
                    PROV_TYPE: "commit",
                    "id": commit["id"],
                    "short_id": commit["short_id"],
                    "title": commit["title"],
                    "message": commit["message"]
                }
            ),

            "resource_version": Entity(
                id=qname(f"{self.project_id}-commit-version-{commit['id']}"),
                label={PROV_TYPE: "commit_version"}
            )
        })

    def events(self, commit: Commit, candidates: Candidates) -> List[Event]:
        """
        Return list of events parsed from *notes* in chronological order.
        """
        prev_event: Optional[Activity] = None
        prev_version: Optional[Entity] = None

        events: List[Event] = []

        for event in self.eventparser.parse(candidates):

            if not prev_event:
                prev_event = Activity(
                    id=qname(f"{self.project_id}-commit-creation-{commit['id']}"),
                    start=None,
                    end=None,
                    label={}
                )
            if not prev_version:
                prev_version = Entity(
                    id=qname(f"{self.project_id}-commit-version-{commit['id']}"),
                    label={}
                )

            events.append(
                Event(**{
                    "initiator": Agent(
                        id=qname(f"{self.project_id}-user-{event.initiator}"),
                        label={
                            PROV_TYPE: "user",
                            PROV_ROLE: "initiator",
                            "name": event.initiator
                        }
                    ),
                    "event": Activity(
                        id=qname(f"{self.project_id}-commit-event-{commit['id']}-{event.id}"),
                        start=event.created_at,
                        end=event.created_at,
                        label=event.label
                    ),
                    "previous_event": prev_event,
                    "resource": Entity(
                        id=qname(f"{self.project_id}-commit-{commit['id']}"),
                        label={}
                    ),
                    "resource_version": Entity(
                        id=qname(f"{self.project_id}-commit-version-{commit['id']}-{event.id}"),
                        label={PROV_TYPE: "commit_version"}
                    ),
                    "previous_resource_version": prev_version
                })
            )

            # update prev_event
            prev_event = Activity(
                id=qname(f"{self.project_id}-commit-event-{commit['id']}-{event.id}"),
                start=None,
                end=None,
                label={}
            )
            # update prev version
            prev_version = Entity(
                id=qname(f"{self.project_id}-commit-version-{commit['id']}-{event.id}"),
                label={PROV_TYPE: "commit_version"}
            )

        return events


@dataclass
class IssueResourceProcessor:

    project_id: str
    eventparser: EventParser = EventParser()

    def run(self, issues: List[Issue], eventables: ParseableContainer) -> List[Resource]:
        """
        Return list of resource life cycles for issues.
        """
        processed = []
        for issue, candidates in zip(issues, eventables):

            processed.append(
                Resource(
                    self.creation(issue),
                    self.events(issue, candidates)
                )
            )

        return processed

    def creation(self, issue: Issue) -> Creation:
        """
        Return creation pack of activities, entities, etc.
        """
        return Creation(**{

            "creator": Agent(
                id=qname(f"{self.project_id}-user-{issue['author']['name']}"),
                label={
                    PROV_TYPE: "user",
                    PROV_ROLE: "creator",
                    "name": issue["author"]["name"]
                }
            ),

            "creation": Activity(
                id=qname(f"{self.project_id}-issue-creation-{issue['id']}"),
                start=ptime(issue["created_at"]),
                end=ptime(issue["created_at"]),
                label={PROV_TYPE: "issue_creation"}
            ),

            "resource": Entity(
                id=qname(f"{self.project_id}-issue-{issue['id']}"),
                label={
                    PROV_TYPE: "issue",
                    "id": issue["id"],
                    "iid": issue["iid"],
                    "title": issue["title"],
                    "description": issue["description"],
                }
            ),

            "resource_version": Entity(
                id=qname(f"{self.project_id}-issue-version-{issue['id']}"),
                label={PROV_TYPE: "issue_version"}
            )
        })

    def events(self, issue: Issue, eventables: Candidates) -> List[Event]:
        """
        Return list of events that occured on *issue* in chronological order, beginning at it's creation.
        """
        events: List[Event] = [
            Event(**{
                "initiator": Agent(
                    id=qname(f"{self.project_id}-user-{issue['author']['name']}"),
                    label={
                        PROV_TYPE: "user",
                        PROV_ROLE: "initiator",
                        "name": issue["author"]["name"]
                    }
                ),

                "event": Activity(
                    id=qname(f"{self.project_id}-issue-event-{issue['id']}-open"),
                    start=ptime(issue["created_at"]),
                    end=ptime(issue["created_at"]),
                    label={
                        PROV_TYPE: "event",
                        "event": "open"
                    }
                ),

                "previous_event": Activity(
                    id=qname(f"{self.project_id}-issue-creation-{issue['id']}"),
                    start=ptime(issue["created_at"]),
                    end=ptime(issue["created_at"]),
                    label={}
                ),

                "resource": Entity(
                    id=qname(f"{self.project_id}-issue-{issue['id']}"),
                    label={
                        PROV_TYPE: "issue",
                        "id": issue["id"],
                        "iid": issue["iid"],
                        "title": issue["title"],
                        "description": issue["description"],
                    }
                ),

                "resource_version": Entity(
                    id=qname(f"{self.project_id}-issue-version-{issue['id']}-open"),
                    label={PROV_TYPE: "issue_version"}
                ),

                "previous_resource_version": Entity(
                    id=qname(f"{self.project_id}-issue-version-{issue['id']}"),
                    label={}
                )
            })
        ]

        # add remaining events
        events.extend(self.event_chain(issue, eventables))

        return events

    def event_chain(self, issue, eventables) -> List[Event]:
        """
        Return list of events that occured on *issue* in chronological order.
        """
        prev_event: Optional[Activity] = None
        prev_version: Optional[Entity] = None

        event_chain: List[Event] = []

        for event in self.eventparser.parse(eventables):

            # Open event was previous event
            if not prev_event:
                prev_event = Activity(
                    id=qname(f"{self.project_id}-issue-event-{issue['id']}-open"),
                    start=ptime(issue["created_at"]),
                    end=ptime(issue["created_at"]),
                    label={}
                )

            # Latest version was the one after open event got applied
            if not prev_version:
                prev_version = Entity(
                    id=qname(f"{self.project_id}-issue-version-{issue['id']}-open"),
                    label={}
                )

            event_chain.append(
                Event(**{
                    "previous_event": prev_event,
                    "previous_resource_version": prev_version,
                    "initiator": Agent(
                        id=qname(f"{self.project_id}-user-{issue['author']['name']}"),
                        label={
                            PROV_TYPE: "user",
                            PROV_ROLE: "initiator",
                            "name": issue["author"]["name"]
                        }
                    ),
                    "event": Activity(
                        id=qname(f"{self.project_id}-issue-event-{issue['id']}-{event.id}"),
                        start=ptime(event.created_at),
                        end=ptime(event.created_at),
                        label=event.label
                    ),
                    "resource": Entity(
                        id=qname(f"{self.project_id}-issue-{issue['id']}"),
                        label={}
                    ),
                    "resource_version": Entity(
                        id=qname(f"{self.project_id}-issue-version-{issue['id']}-{event.id}"),
                        label={PROV_TYPE: "issue_version"}
                    ),
                })
            )

            # Update previous event
            prev_event = Activity(
                id=qname(f"{self.project_id}-issue-event-{issue['id']}-{event.id}"),
                start=None,
                end=None,
                label={}
            )

            # Update previous version
            prev_version = Entity(
                id=qname(f"{self.project_id}-issue-version-{issue['id']}-{event.id}"),
                label={PROV_TYPE: "issue_version"}
            )

        return event_chain


@dataclass
class MergeRequestResourceProcessor:

    project_id: str
    eventparser: EventParser = EventParser()

    def run(self, merge_requests: List[MergeRequest], eventables: ParseableContainer) -> List[Resource]:
        """
        Return the resource life cycle of each merge request in
        *merge_requests*.

        Parse labels, awards, notes and note awards as eventables.
        """
        processed: List[Resource] = []

        for mr, candidates in zip(merge_requests, eventables):
            processed.append(
                Resource(
                    self.creation(mr),
                    self.events(mr, candidates)
                )
            )

        return processed

    def creation(self, merge_request: MergeRequest) -> Creation:
        """
        Return creation pack for *merge_request*.
        """
        return Creation(**{

            "creator": Agent(
                id=qname(f"{self.project_id}-user-{merge_request['author']['name']}"),
                label={
                    PROV_TYPE: "user",
                    PROV_ROLE: "creator",
                    "name": merge_request["author"]["name"]
                }
            ),

            "creation": Activity(
                id=qname(f"{self.project_id}-merge-request-creation-{merge_request['id']}"),
                start=ptime(merge_request["created_at"]),
                end=ptime(merge_request["created_at"]),
                label={PROV_TYPE: "merge_request_creation"}
            ),

            "resource": Entity(
                id=qname(f"{self.project_id}-merge-request-{merge_request['id']}"),
                label={
                    PROV_TYPE: "merge_request",
                    "id": merge_request["id"],
                    "iid": merge_request["iid"],
                    "title": merge_request["title"],
                    "description": merge_request["description"],
                    "source_project_id": merge_request["source_project_id"],
                    "target_project_id": merge_request["target_project_id"],
                    "source_branch": merge_request["source_branch"],
                    "target_branch": merge_request["target_branch"]
                }
            ),

            "resource_version": Entity(
                id=qname(f"{self.project_id}-merge-request-version-{merge_request['id']}"),
                label={PROV_TYPE: "merge_request_version"}
            )
        })

    def events(self, merge_request: MergeRequest, eventables: Candidates) -> List[Event]:
        """
        Return list of events for *merge_request* from *eventables* in
        chronological order.
        """
        events: List[Event] = [
            Event(**{
                "initiator": Agent(
                    id=qname(f"{self.project_id}-user-{merge_request['author']['name']}"),
                    label={
                        PROV_TYPE: "user",
                        PROV_ROLE: "initiator",
                        "name": merge_request["author"]["name"]
                    }
                ),

                "event": Activity(
                    id=qname(f"{self.project_id}-merge-request-event-{merge_request['id']}-open"),
                    start=ptime(merge_request["created_at"]),
                    end=ptime(merge_request["created_at"]),
                    label={
                        PROV_TYPE: "event",
                        "event": "open"
                    }
                ),

                "previous_event": Activity(
                    id=qname(f"{self.project_id}-merge-request-creation-{merge_request['id']}"),
                    start=None,
                    end=None,
                    label={}
                ),

                "resource": Entity(
                    id=qname(f"{self.project_id}-merge-request-{merge_request['id']}"),
                    label={
                        PROV_TYPE: "merge_request",
                        "id": merge_request["id"],
                        "iid": merge_request["iid"],
                        "title": merge_request["title"],
                        "description": merge_request["description"],
                        "source_project_id": merge_request["source_project_id"],
                        "target_project_id": merge_request["target_project_id"],
                        "source_branch": merge_request["source_branch"],
                        "target_branch": merge_request["target_branch"]
                    }
                ),

                "resource_version": Entity(
                    id=qname(f"{self.project_id}-merge-request-version-{merge_request['id']}-open"),
                    label={PROV_TYPE: "merge_request_version"}
                ),

                "previous_resource_version": Entity(
                    id=qname(f"{self.project_id}-merge-request-version-{merge_request['id']}"),
                    label={}
                )
            })
        ]

        # add remaining events
        events.extend(self.event_chain(merge_request, eventables))

        return events

    def event_chain(self, merge_request: MergeRequest, eventables: Candidates) -> List[Event]:
        """
        Parse events and return chain of events in chronological order.

        Hint: to relate to previous_events or previous_versions
        you only need to fill the id field.
        """
        prev_event: Optional[Activity] = None
        prev_version: Optional[Entity] = None

        event_chain: List[Event] = []

        for event in self.eventparser.parse(eventables):

            # Open event was previous event
            if not prev_event:
                prev_event = Activity(
                    id=qname(f"{self.project_id}-merge-request-event-{merge_request['id']}-open"),
                    start=None,
                    end=None,
                    label={}
                )

            # Latest version was the one after open event got applied
            if not prev_version:
                prev_version = Entity(
                    id=qname(f"{self.project_id}-merge-request-version-{merge_request['id']}-open"),
                    label={}
                )

            event_chain.append(
                Event(**{
                    "previous_event": prev_event,
                    "previous_resource_version": prev_version,
                    "initiator": Agent(
                        # Initiator of event
                        id=qname(f"{self.project_id}-user-{merge_request['author']['name']}"),
                        label={
                            PROV_TYPE: "user",
                            PROV_ROLE: "initiator",
                            "name": merge_request["author"]["name"]
                        }
                    ),
                    "event": Activity(
                        # Event activity
                        id=qname(f"{self.project_id}-merge-request-event-{merge_request['id']}-{event.id}"),
                        start=ptime(event.created_at),
                        end=ptime(event.created_at),
                        label=event.label
                    ),
                    "resource": Entity(
                        # Original entity of merge request
                        id=qname(f"{self.project_id}-merge-request-{merge_request['id']}"),
                        label={}
                    ),
                    "resource_version": Entity(
                        # Merge Request state after latest event got appplied
                        id=qname(f"{self.project_id}-merge-request-version-{merge_request['id']}-{event.id}"),
                        label={PROV_TYPE: "merge_request_version"}
                    ),
                })
            )

            # Update previous event
            prev_event = Activity(
                id=qname(f"{self.project_id}-merge-request-event-{merge_request['id']}-{event.id}"),
                start=None,
                end=None,
                label={}
            )

            # Update previous version
            prev_version = Entity(
                id=qname(f"{self.project_id}-merge-request-version-{merge_request['id']}-{event.id}"),
                label={PROV_TYPE: "merge_request_version"}
            )

        return event_chain
