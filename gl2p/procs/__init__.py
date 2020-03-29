from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Union

from gl2p.utils.types import Commit, Diff, Issue, MergeRequest

from .history import FileNameHistory
from .meta import (Addition, Author, Candidates, CommitCreationPackage,
                   CommitModelPackage, Committer, CreationPackage, Creator,
                   Deletion, EventPackage, File, FileVersion, MetaCommit,
                   MetaCreation, MetaResource, MetaResourceVersion,
                   Modification, ParseableContainer, ResourceModelPackage)
from .parser import parse


class CommitProcessor:
    """
    Converts commits and diffs to commit model packages.
    Link between model implementation and API resources.
    """
    def __init__(self, commits: List[Commit], diffs: List[Diff]) -> None:
        self.diffs = diffs
        self.commits = commits
        self.lookup: Dict[str, Commit] = {commit["id"]: commit for commit in commits}
        self.history: FileNameHistory = FileNameHistory()
        self.history.compute(commits, diffs)

    def run(self) -> List[CommitModelPackage]:
        pkgs: List[CommitModelPackage] = []

        for commit, diff in zip(self.commits, self.diffs):
            # fetch the parents of the current commit
            parents = [self.lookup[psha] for psha in commit["parent_ids"]]

            pkg = CommitModelPackage(
                # compute author of the current commit
                Author.from_commit(commit).atomize(),
                # compute committer of the current commit
                Committer.from_commit(commit).atomize(),
                # compute commit activity for the current commit
                MetaCommit.from_commit(commit).atomize(),
                # compute commit activities
                # for all parent commits to the current commit
                [MetaCommit.from_commit(parent).atomize() for parent in parents],
                # compute the change set
                self.compute_change_set(commit, diff)
            )
            # add commit model package to package list
            pkgs.append(pkg)
        return pkgs

    def compute_change_set(self, commit: Commit, diff: Diff) -> List[Union[Addition, Deletion, Modification]]:
        """
        """
        change_set: List[Union[Addition, Deletion, Modification]] = []

        for entry in diff:
            sha = commit["id"]
            new_path = entry["new_path"]
            old_path = entry["old_path"]

            # determine original file name
            # use this name in the identifier of subsequent versions
            origin = self.history.get(sha, new_path)

            # compute file entity for the original file
            f_origin = File.create(origin).atomize()

            # compute file version entity for the current file
            f_curr = FileVersion.create(origin, old_path, new_path, sha).atomize()

            # compute file version entities based on
            # the naive assumption that the versions
            # of directly preceeding commits where used

            # therefore create a file version for each preceeding commit
            # this can be faulty as this could assign a file version
            # to a branch that didn't include the file in the first place

            # this also bares the side effect that the provenance graph
            # will hold more file version entities than versions a file
            # ever existed
            f_prevs = [
                FileVersion.create(origin, old_path, new_path, psha).atomize()
                for psha in commit["parent_ids"]
            ]

            # based on what action the diff entry describes
            # choose the appropriate context subpackage
            if entry["new_file"]:
                # added new file -> Addition
                change_set.append(Addition(f_origin, f_curr))
                continue
            elif entry["deleted_file"]:
                # deleted file   -> Deletion
                change_set.append(Deletion(f_origin, f_curr))
                continue
            else:
                # modified file  -> Modification
                change_set.append(Modification(f_origin, f_curr, f_prevs))
                continue
        # return list of file change packages (change set)
        return change_set


class CommitResourceProcessor:
    """
    Converts commits, and notes to resource model packages.
    Link between model implementation and API resources.
    """
    def __init__(self, commits: List[Commit], parseables: ParseableContainer) -> None:
        self.commits: List[Commit] = commits
        self.parseables: ParseableContainer = parseables

    def run(self) -> List[ResourceModelPackage]:
        pkgs: List[ResourceModelPackage] = []

        for commit, candidates in zip(self.commits, self.parseables):
            # creation subpackage
            creation = CommitCreationPackage(
                # extract committer
                Committer.from_commit(commit).atomize(),
                # extract commit activity
                MetaCommit.from_commit(commit).atomize(),
                # extract creation activity
                MetaCreation.from_commit(commit).atomize(),
                # compute commit resource
                MetaResource.from_commit(commit).atomize(),
                # compute commit resource version
                MetaResourceVersion.from_commit(commit).atomize()
            )
            # event chain subpackage
            event_chain = self.compute_event_chain(commit, candidates)

            # prepend package to event chain
            # that represents the creation of the resource
            event_chain.appendleft(EventPackage(
                creation.committer,
                creation.commit,
                creation.resource,
                creation.resource_version
            ))
            # combine subpackages to resource package
            # add resource package to list of computed packages
            pkgs.append(ResourceModelPackage(creation, event_chain))
        return pkgs

    def compute_event_chain(self, commit: Commit, candidates: Candidates) -> Deque[EventPackage]:
        chain: Deque[EventPackage] = deque()
        # parser returns events ordered by date ascending
        # (from earliest to latest, past to present)

        for meta_event in parse(candidates):
            # event package creation
            pkg = EventPackage(
                # extract initiator from parsed meta_event
                meta_event.initiator.atomize(),
                # convert meta event to PROV activity
                meta_event.atomize(),
                # compute original resource
                MetaResource.from_commit(commit).atomize(),
                # compute commit resource version
                MetaResourceVersion.from_commit(commit, meta_event).atomize()
            )
            # add package to package chain
            chain.append(pkg)
        return chain


class IssueResourceProcessor:
    """
    Converts issues, notes, label events and award emoji to resource model packages.
    Link between model implementation and API resources.
    """
    def __init__(self, issues: List[Issue], parseables: ParseableContainer) -> None:
        self.issues: List[Issue] = issues
        self.parseables: ParseableContainer = parseables

    def run(self) -> List[ResourceModelPackage]:
        pkgs: List[ResourceModelPackage] = []

        for issue, candidates in zip(self.issues, self.parseables):
            # creation subpackage
            creation = CreationPackage(
                # compute creator for current issue
                Creator.from_issue(issue).atomize(),
                # compute creation activity for current issue
                MetaCreation.from_issue(issue).atomize(),
                # compute issue original for current issue
                MetaResource.from_issue(issue).atomize(),
                # compute first resource version for current issue
                MetaResourceVersion.from_issue(issue).atomize()
            )
            # event chain
            event_chain = self.compute_event_chain(issue, candidates)
            # prepend event package representing
            # the creation of the resource to the event chain
            event_chain.appendleft(EventPackage(
                creation.creator,
                creation.creation,
                creation.resource,
                creation.resource_version
            ))
            # add resource package to package list
            pkgs.append(ResourceModelPackage(creation, event_chain))
        return pkgs

    def compute_event_chain(self, issue: Issue, candidates: Candidates) -> Deque[EventPackage]:
        chain: Deque[EventPackage] = deque()

        for meta_event in parse(candidates):
            pkg = EventPackage(
                # extract initiator from parsed meta event
                meta_event.initiator.atomize(),
                # convert parsed meta event to PROV activity
                meta_event.atomize(),
                # compute issue resource original
                MetaResource.from_issue(issue).atomize(),
                # compute issue resource version
                MetaResourceVersion.from_issue(issue, meta_event).atomize()
            )
            # add event package to event chain
            chain.append(pkg)
        return chain


class MergeRequestResourceProcessor:
    """
    Converts merge requests, notes, label events and award emoji to resource model packages.
    Link between model implementation and API resources.
    """
    def __init__(self, merge_requests: List[MergeRequest], parseables: ParseableContainer) -> None:
        self.merge_requests: List[MergeRequest] = merge_requests
        self.parseables: ParseableContainer = parseables

    def run(self) -> List[ResourceModelPackage]:
        pkgs: List[ResourceModelPackage] = []

        for merge_request, candidates in zip(self.merge_requests, self.parseables):
            creation = CreationPackage(
                # compute merge request creator
                Creator.from_merge_request(merge_request).atomize(),
                # compute merge request creation activity
                MetaCreation.from_merge_request(merge_request).atomize(),
                # compute merge request resource original
                MetaResource.from_merge_request(merge_request).atomize(),
                # compute merge request resource version
                MetaResourceVersion.from_merge_request(merge_request).atomize()
            )
            # compute event chain
            event_chain = self.compute_event_chain(merge_request, candidates)

            # prepend event package representing
            # the creation of the resource to the event chain
            event_chain.appendleft(EventPackage(
                creation.creator,
                creation.creation,
                creation.resource,
                creation.resource_version
            ))
            pkgs.append(ResourceModelPackage(creation, event_chain))
        return pkgs

    def compute_event_chain(self, merge_request: MergeRequest, candidates: Candidates) -> Deque[EventPackage]:
        chain: Deque[EventPackage] = deque()

        for meta_event in parse(candidates):
            pkg = EventPackage(
                # extract initiator from meta event
                meta_event.initiator.atomize(),
                # convert meta event to PROV activity
                meta_event.atomize(),
                # compute merge request resource original
                MetaResource.from_merge_request(merge_request).atomize(),
                # compute merge request resource version
                MetaResourceVersion.from_merge_request(merge_request, meta_event).atomize()
            )
            chain.append(pkg)
        return chain
