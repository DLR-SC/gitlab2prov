from collections import defaultdict, namedtuple
import prov.model as prov
from prov.constants import PROV_LABEL, PROV_TYPE, PROV_ROLE
from gl2p.commons import FileAction


class Translator:

    def __init__(self):
        self.prov = prov.ProvDocument()

    def translate(self, data, *args, **kwargs):
        """
        Abstract method to translate data of some kind to prov vocabulary
        """
        raise NotImplementedError()

    def clean(self):
        # NOTE: unification removes duplicates by deleting multiplicities with same identifier
        # can also be used to remove duplicated relations, iff relation has identifier
        self.prov = self.prov.unified()


class CommitTranslator(Translator):

    def __init__(self):
        super().__init__()
        self.__file_track = defaultdict(set)
        # TODO: correct namespace definition for project
        self.prov.set_default_namespace("https://example.org")

    def translate(self, data, *args, **kwargs):
        for commit in data:
            names = self._format_names(commit)

            # keep track of file aliases over time
            self._track_file(commit)

            # NOTE: comment out times for clarity in diagrams
            # NOTE: this can also be done by assigning start and end time attributes for the respective activities.
            self.prov.wasStartedBy(names.commit, time=commit.authored_date)
            self.prov.wasEndedBy(names.commit, time=commit.committed_date)
            self.prov.activity(identifier=names.commit, other_attributes={PROV_LABEL: commit.message})
            
            # NOTE: wasInformedBy relation documents the chain of commits, much like a commit graph
            for parent in names.parents:
                self.prov.wasInformedBy(names.commit, parent, identifier=names.commit+parent)
            
            # NOTE: stem file tracking allows mapping of a file alias to its original file entity
            stem_file = self._compute_stem_file(commit.file_path_used)
            self.prov.agent(names.author)
            self.prov.agent(names.committer)
            self.prov.wasAssociatedWith(names.commit, names.author, other_attributes={PROV_ROLE: "author"})
            self.prov.wasAssociatedWith(names.commit, names.committer, other_attributes={PROV_ROLE: "committer"})
            
            # NOTE: depending on the file action, decide which prov vocabulary to add
            if commit.file_action == FileAction.ADDED:
                self.prov.entity(names.file, other_attributes={PROV_LABEL: commit.file_path_used})
            if commit.file_action == FileAction.MODIFIED:
                # TODO: fix issue with merge commits.
                # what files should be "used"
                # what files should be "derived"
                for used_file in names.used_files:
                    self.prov.used(names.commit, used_file, time=commit.authored_date)
                    self.prov.wasDerivedFrom(names.generated_file, used_file, names.commit)
            if commit.file_action == FileAction.DELETED:
                for used_file in names.used_files:
                    self.prov.wasInvalidatedBy(used_file, names.commit, time=commit.authored_date)
            else:
                self.prov.specializationOf(names.generated_file, f"file-{self._namify(stem_file)}")
                self.prov.wasGeneratedBy(names.generated_file, names.commit, time=commit.authored_date)
                self.prov.entity(identifier=names.generated_file)
                self.prov.wasAttributedTo(names.generated_file, names.author)

    def _track_file(self, commit):
        if commit.file_path_used != commit.file_path_generated:
            self.__file_track[commit.file_path_used].add(commit.file_path_generated)

    def _compute_stem_file(self, alias):
        lookup = dict()
        for key, vset in self.__file_track.items():
            for value in vset:
                lookup[value] = key
        while lookup.get(alias):
            alias = lookup[alias]
        return alias

    def _namify(self, string):
        replacements = {"-": ["/", ".", " "]}
        for rep, sublist in replacements.items():
            for sub in sublist:
                string = string.replace(sub, rep)
        return string

    def _format_names(self, commit):
        namespace = "commit parents author committer file generated_file used_files"
        Names = namedtuple("Names", namespace)
        return Names(*[
            f"commit-{commit.id}",
            [f"commit-{pid}" for pid in commit.parent_ids],
            f"user-{self._namify(commit.author_name)}",
            f"user-{self._namify(commit.committer_name)}",
            f"file-{self._namify(commit.file_path_used)}",
            f"file-{self._namify(commit.file_path_generated)}_commit-{commit.id}",
            [f"file-{self._namify(commit.file_path_used)}_commit-{pid}" for pid in commit.parent_ids]])
