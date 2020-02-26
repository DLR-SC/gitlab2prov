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
from gl2p.utils.objects import (CommitResource, Event, Resource, Creation, Agent, GL2PEvent,
                                Entity, Activity, CommitCreation, ParseableContainer,
                                Candidates, Addition, Deletion, Modification)
from gl2p.utils.types import Commit, Issue, MergeRequest, Diff
from gl2p.utils.helpers import qname, ptime


def author(commit: Commit) -> Agent:
    """
    Return the author of *commit* as a PROV agent.
    """
    id_ = qname(f"user-{commit['author_name']}")
    label = {PROV_TYPE: "user", PROV_ROLE: "author", "name": commit["author_name"]}
    return Agent(id_, label)


def committer(commit: Commit) -> Agent:
    """
    Return the committer of *commit* as a PROV agent.
    """
    id_ = qname(f"user-{commit['committer_name']}")
    label = {PROV_TYPE: "user", PROV_ROLE: "committer", "name": commit["committer_name"]}
    return Agent(id_, label)


def commit_activity(commit: Commit) -> Activity:
    """
    Return the commit activity denoted by *commit*.
    """
    id_ = qname(f"commit-{commit['id']}")
    start = ptime(commit["authored_date"])
    end = ptime(commit["committed_date"])
    label = {PROV_TYPE: "commit", "sha": commit["id"], "title": commit["title"], "message": commit["message"]}
    return Activity(id_, start, end, label)


def parent_commit_activities(commit: Commit, all_commits: List[Commit]) -> List[Activity]:
    """
    Return the parent commit activities of *commit*.

    Build a lookup of all commits.
    """
    # TODO: cache the lookup, this is inefficient.
    # NOTE: or outsource it, should be fine.
    clookup = {c["id"]: c for c in all_commits}

    # return list of parenting commit activities
    return [commit_activity(clookup[pid]) for pid in commit["parent_ids"]]


def file_version(original_name: str, version_id: str, old_path: Optional[str] = "", new_path: Optional[str] = "") -> Entity:
    """
    Return file version id.
    """
    id_ = qname(f"file-{original_name}-{version_id}")
    label = {PROV_TYPE: "file-version"}

    if old_path and new_path:
        label.update({"old_path": old_path, "new_path": new_path})

    return Entity(id_, label)


def commit_resource_creation(commit: Commit) -> Activity:
    """
    Return activity that denotes the creation of the commit resource
    associated with *commit*.
    """
    id_ = qname(f"commit-resource-creation-{commit['id']}")
    start = ptime(commit["committed_date"])
    end = ptime(commit["committed_date"])
    label = {PROV_TYPE: "commit_resource_creation"}
    return Activity(id_, start, end, label)


def commit_resource_entity(commit: Commit) -> Entity:
    """
    Return entity that represents the original resource version of the
    commit resource represented by *commit*.
    """
    id_ = qname(f"commit-resource-{commit['id']}")
    label = {PROV_TYPE: "commit_resource"}

    label.update({
        "id": commit["id"],
        "short_id": commit["short_id"],
        "title": commit["title"],
        "message": commit["message"]
    })

    return Entity(id_, label)


def commit_resource_version_entity(commit: Commit, postfix: str = "") -> Entity:
    """
    Return entity that represents a version of the commit resource
    represented by *commit*.
    """
    id_ = qname(f"commit-resource-{commit['id']}{'-' if postfix else ''}{postfix}")
    label = {PROV_TYPE: "commit_resource_version"}
    return Entity(id_, label)


def event_initiator_agent(event: GL2PEvent) -> Agent:
    """
    Return agent that represents the initiator of *event*.
    """
    id_ = qname(f"user-{event.initiator}")
    label = {PROV_TYPE: "user", PROV_ROLE: "event_initiator", "name": event.initiator}
    return Agent(id_, label)


def commit_resource_event_activity(event: GL2PEvent) -> Activity:
    """
    Return activity representing an event that occured on a commit
    resource.
    """
    id_ = qname(f"commit-resource-event-{event.id}")
    start = ptime(event.created_at)
    end = ptime(event.created_at)
    label = event.label

    return Activity(id_, start, end, label)


def issue_creator(issue: Issue) -> Agent:
    """
    Return agent that represents the author of *issue*.
    """
    id_ = qname(f"user-{issue['author']['name']}")
    label = {PROV_TYPE: "user", PROV_ROLE: "issue_creator", "name": issue["author"]["name"]}
    return Agent(id_, label)


def issue_creation_activity(issue: Issue) -> Activity:
    """
    Return activity that represents the creation of *issue*.
    """
    id_ = qname(f"issue-creation-{issue['iid']}")
    start = ptime(issue["created_at"])
    end = ptime(issue["created_at"])
    label = {PROV_TYPE: "issue_creation"}
    return Activity(id_, start, end, label)


def issue_resource_entity(issue: Issue) -> Entity:
    """
    Return entity that represents the original *issue* version.
    """
    id_ = qname(f"issue-resource-{issue['iid']}")
    label = {PROV_TYPE: "issue"}

    label.update({
        "id": issue["id"],
        "iid": issue["iid"],
        "title": issue["title"],
        "description": issue["description"]
    })

    return Entity(id_, label)


def issue_resource_version_entity(issue: Issue, postfix: str = "") -> Entity:
    """
    Return entity that represents a version of resource *issue*.
    """
    id_ = qname(f"issue-resource-version-{issue['iid']}{'-' if postfix else ''}{postfix}")
    label = {PROV_TYPE: "issue_resource_version"}
    return Entity(id_, label)


def issue_resource_event_activity(issue: Issue, event: GL2PEvent) -> Activity:
    """
    Return activity that represents an event occurring on an issue resource.
    """
    # TODO: flesh out information in label
    id_ = qname(f"issue-resource-event-{issue['iid']}-{event.id}")
    start = ptime(event.created_at)
    end = ptime(event.created_at)
    label = event.label
    return Activity(id_, start, end, label)


def merge_request_resource_event_activity(merge_request: MergeRequest, event: GL2PEvent) -> Activity:
    """
    Return activity that represents an event occurring on a merge request resource.
    """
    id_ = qname(f"merge-request-resource-event-{merge_request['iid']}-{event.id}")
    start = ptime(event.created_at)
    end = ptime(event.created_at)
    label = event.label
    return Activity(id_, start, end, label)


def merge_request_creator(merge_request: MergeRequest) -> Agent:
    """
    Return agent that represents the creator of *merge_request*.
    """
    id_ = qname(f"user-{merge_request['author']['name']}")
    label = {PROV_TYPE: "user", PROV_ROLE: "merge_request_creator", "name": merge_request["author"]["name"]}
    return Agent(id_, label)


def merge_request_creation_activity(merge_request: MergeRequest) -> Activity:
    """
    Return activity that represents the creation of a merge request resource.
    """
    id_ = qname(f"merge-request-creation-{merge_request['iid']}")
    start = ptime(merge_request["created_at"])
    end = ptime(merge_request["created_at"])
    label = {PROV_TYPE: "merge_request_creation"}
    return Activity(id_, start, end, label)


def merge_request_resource_entity(merge_request: MergeRequest) -> Entity:
    """
    Return entity that represents the original version of a merge request resource.
    """
    id_ = qname(f"merge-request-resource-{merge_request['iid']}")
    label = {PROV_TYPE: "merge_request"}

    label.update({
        "id": merge_request["id"],
        "iid": merge_request["iid"],
        "title": merge_request["title"],
        "description": merge_request["description"],
        "source_project_id": merge_request["source_project_id"],
        "target_project_id": merge_request["target_project_id"],
        "source_branch": merge_request["source_branch"],
        "target_branch": merge_request["target_branch"]
    })

    return Entity(id_, label)


def merge_request_resource_version_entity(merge_request: MergeRequest, postfix: str = "") -> Entity:
    """
    Return entity that represents the version of a merge reques resource.
    """
    id_ = qname(f"merge-request-resource-version-{merge_request['iid']}{'-' if postfix else ''}{postfix}")
    label = {PROV_TYPE: "merge_request_resource_version"}
    return Entity(id_, label)


class CommitProcessor:
    """
    Preprocess commit data before dumping into PROV model.
    """
    history: FileNameHistory = FileNameHistory()

    def run(self, commits: List[Commit], diffs: List[Diff]) -> List[CommitResource]:
        """
        """
        self.history.compute(commits, diffs)

        processed = []

        for commit, diff in zip(commits, diffs):
            processed.append(
                CommitResource(
                    author(commit),
                    committer(commit),
                    commit_activity(commit),
                    parent_commit_activities(commit, commits),
                    self.changes(commit, diff)
                )
            )
        return processed

    def changes(self, commit: Commit, diff: Diff) -> List[Union[Addition, Deletion, Modification]]:
        """
        Return diff entries parsed as FileChanges.
        """
        changes = []  # type: List[Union[Addition, Deletion, Modification]]

        for entry in diff:

            # get original file name of file denoted in diff entry
            original = self.history.get(commit["id"], entry["new_path"])

            f = Entity(id=qname(f"file-{original}"), label={PROV_TYPE: "file"})
            f_version = file_version(original, commit["id"], entry["old_path"], entry["new_path"])

            if entry["new_file"]:
                changes.append(Addition(f, f_version))

            elif entry["deleted_file"]:
                changes.append(Deletion(f, f_version))

            elif entry["new_path"] != entry["old_path"]:
                previous_f_versions = [file_version(original, pid) for pid in commit["parent_ids"]]
                changes.append(Modification(f, f_version, previous_f_versions))

        return changes


@dataclass
class CommitResourceProcessor:
    """
    Preprocess commit resource data before handing over to model population.
    """
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
        return CommitCreation(
            committer(commit),
            commit_activity(commit),
            commit_resource_creation(commit),
            commit_resource_entity(commit),
            commit_resource_version_entity(commit, postfix="")
        )

    def events(self, commit: Commit, candidates: Candidates) -> List[Event]:
        """
        Return list of events parsed from *notes* in chronological order.
        """
        previous_event = commit_resource_creation(commit)
        previous_resource_version = commit_resource_version_entity(commit, postfix="")

        events = []
        for event in self.eventparser.parse(candidates):

            event_activity = commit_resource_event_activity(event)

            events.append(
                Event(
                    event_initiator_agent(event),
                    commit_resource_event_activity(event),
                    previous_event,
                    commit_resource_entity(commit),
                    commit_resource_version_entity(commit, postfix=event.id),
                    previous_resource_version
                )
            )
            # update latest event
            previous_event = event_activity
            # update latest resource version
            previous_resource_version = commit_resource_version_entity(commit, postfix=event.id)

        return events


@dataclass
class IssueResourceProcessor:

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
        return Creation(
            issue_creator(issue),  # author of issue is creator
            issue_creation_activity(issue),
            issue_resource_entity(issue),
            issue_resource_version_entity(issue, postfix=""),
        )

    def events(self, issue: Issue, eventables: Candidates) -> List[Event]:
        """
        """
        previous_resource_version = issue_resource_version_entity(issue, postfix="")
        previous_event = issue_creation_activity(issue)

        events = []

        for event in self.eventparser.parse(eventables):

            events.append(
                Event(
                    event_initiator_agent(event),
                    issue_resource_event_activity(issue, event),
                    previous_event,
                    issue_resource_entity(issue),
                    issue_resource_version_entity(issue, postfix=event.id),
                    previous_resource_version
                )
            )
            # update latest events, versions
            previous_event = issue_resource_event_activity(issue, event)
            previous_resource_version = issue_resource_version_entity(issue, event.id)

        return events


@dataclass
class MergeRequestResourceProcessor:

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
        return Creation(
            merge_request_creator(merge_request),
            merge_request_creation_activity(merge_request),
            merge_request_resource_entity(merge_request),
            merge_request_resource_version_entity(merge_request, postfix="")
        )

    def events(self, merge_request: MergeRequest, eventables: Candidates) -> List[Event]:
        """
        Return list of events for *merge_request* from *eventables* in
        chronological order.
        """
        events: List[Event] = []

        previous_event = merge_request_creation_activity(merge_request)
        previous_version = merge_request_resource_version_entity(merge_request, postfix="")

        for event in self.eventparser.parse(eventables):

            events.append(
                Event(
                    event_initiator_agent(event),
                    merge_request_resource_event_activity(merge_request, event),
                    previous_event,
                    merge_request_resource_entity(merge_request),
                    merge_request_resource_version_entity(merge_request, postfix=event.id),
                    previous_version
                )
            )

            previous_event = merge_request_resource_event_activity(merge_request, event)
            previous_version = merge_request_resource_version_entity(merge_request, postfix=event.id)

        return events
