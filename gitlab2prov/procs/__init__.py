from __future__ import annotations

from typing import Dict, List, Union, Any, Set

from gitlab2prov.utils.types import Commit, Diff, Issue, MergeRequest, Label, Note, Award

from gitlab2prov.procs.history import FileNameHistory
from gitlab2prov.procs.meta import Addition, Deletion, Modification, CommitCreationPackage, ResourceCreationPackage, \
    CommitModelPackage, ResourceModelPackage, File, FileVersion, MetaEvent, EventPackage, TagPackage, ReleasePackage, ReleaseTagPackage
from gitlab2prov.procs.parser import parse


class CommitProcessor:
    @staticmethod
    def process(commits: List[Commit], diffs: List[Diff]) -> List[CommitModelPackage]:
        packages = []
        commits = {commit["id"]: commit for commit in commits}
        for commit, parsed_diff in zip(commits.values(), CommitProcessor.parse_diffs(commits, diffs)):
            parents = []
            for parent_id in commit["parent_ids"]:
                parent = commits.get(parent_id)
                if parent:
                    parents.append(parent)
            package = CommitModelPackage.from_commit(commit=commit, parents=parents, diff=parsed_diff)
            packages.append(package)
        return packages

    @staticmethod
    def parse_diffs(commits: Dict[str, Commit],
                    diffs: List[Diff]) -> List[List[Union[Addition, Deletion, Modification]]]:
        file_name_history = FileNameHistory.compute(list(commits.values()), diffs)

        parsed = []
        for commit, diff in zip(commits.values(), diffs):

            parsed_diff = []
            for entry in diff:
                original_file_name = file_name_history.get(commit["id"], entry["new_path"])
                used_versions = file_name_history.get_versions(commit["id"], original_file_name)
                parsed_entry = CommitProcessor.parse_diff_entry(
                    diff_entry=entry,
                    commit=commit,
                    original_file_name=original_file_name,
                    used_versions=used_versions)
                parsed_diff.append(parsed_entry)

            parsed.append(parsed_diff)
        return parsed

    @staticmethod
    def parse_diff_entry(diff_entry: Dict[str, Any],
                         commit: Commit,
                         original_file_name: str,
                         used_versions: Set[str]) -> Union[Addition, Deletion, Modification]:
        parsed_origin = File.create(original_file_name).to_prov_element()
        parsed_current = FileVersion.create(
            original_file_name,
            diff_entry["old_path"],
            diff_entry["new_path"],
            commit["id"]).to_prov_element()

        if diff_entry["new_file"]:
            return Addition(parsed_origin, parsed_current)
        elif diff_entry["deleted_file"]:
            return Deletion(parsed_origin, parsed_current)

        parsed_previous = []
        for version in used_versions:
            previous = FileVersion.create(
                original_file_name,
                diff_entry["old_path"],
                diff_entry["new_path"],
                version).to_prov_element()
            parsed_previous.append(previous)

        return Modification(parsed_origin, parsed_current, parsed_previous)


class EventChainBuilder:
    @staticmethod
    def compute_event_chain(creation: Union[CommitCreationPackage, ResourceCreationPackage],
                            parsed_events: List[MetaEvent]) -> List[EventPackage]:
        creation_event = EventPackage.from_creation(creation)
        chain = [creation_event]
        if not parsed_events:
            return chain
        chain.append(EventPackage.from_meta_events(latest=parsed_events[0], previous=creation_event))
        for n, current in enumerate(parsed_events[1:]):
            previous = chain[n+1]
            chain.append(EventPackage.from_meta_events(current, previous))
        return chain


class CommitResourceProcessor:
    @staticmethod
    def process(commits: List[Commit], notes: List[List[Note]]) -> List[ResourceModelPackage]:
        packages = []
        for commit, notes in zip(commits, notes):
            creation = CommitCreationPackage.from_commit(commit)
            parsed_events = parse(notes=notes)
            event_chain = EventChainBuilder.compute_event_chain(creation, parsed_events)
            packages.append(ResourceModelPackage(creation=creation, event_chain=event_chain))
        return packages


class IssueResourceProcessor:
    @staticmethod
    def process(issues: List[Issue],
                notes: List[List[Note]],
                labels: List[List[Label]],
                awards: List[List[Award]],
                note_awards: List[List[Award]]) -> List[ResourceModelPackage]:
        packages = []
        zipped_annotations = zip(notes, labels, awards, note_awards)
        for issue, annotation in zip(issues, zipped_annotations):
            creation = ResourceCreationPackage.from_issue(issue)
            parsed_events = parse(*annotation)
            event_chain = EventChainBuilder.compute_event_chain(creation, parsed_events)
            packages.append(ResourceModelPackage(creation, event_chain))
        return packages


class MergeRequestResourceProcessor:
    @staticmethod
    def process(merge_requests: List[MergeRequest],
                notes: List[List[Note]],
                labels: List[List[Label]],
                awards: List[List[Award]],
                note_awards: List[List[Award]]) -> List[ResourceModelPackage]:
        packages = []
        zipped_annotations = zip(notes, labels, awards, note_awards)
        for merge_request, annotation in zip(merge_requests, zipped_annotations):
            creation = ResourceCreationPackage.from_merge_request(merge_request)
            parsed_events = parse(*annotation)
            event_chain = EventChainBuilder.compute_event_chain(creation, parsed_events)
            packages.append(ResourceModelPackage(creation, event_chain))
        return packages

class ReleaseTagProcessor:
    def process(releases, tags):
        tags = {tag["name"]: tag for tag in tags}
        releases = {release["tag_name"]: release for release in releases}

        packages = []
        for tag_name in tags.keys() | releases.keys():
            if tag_name in tags:
                tag = tags[tag_name]
                commit = tag["commit"]
                tag_pkg = TagPackage.from_tag(tag)
                commit_pkg = CommitCreationPackage.from_commit(commit)
            else:
                tag_pkg = None
                commit_pkg = None

            if tag_name not in releases:
                packages.append(ReleaseTagPackage(None, tag_pkg, commit_pkg))
            else:
                release = releases[tag_name]
                release_pkg = ReleasePackage.from_release(release)
                packages.append(ReleaseTagPackage(release_pkg, tag_pkg, commit_pkg))
        return packages
