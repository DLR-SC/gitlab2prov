from collections import defaultdict, deque, namedtuple
import prov.model as pm
from prov.constants import PROV_LABEL, PROV_ROLE
from gl2p.commons import FileAction


class Translator:

    def __init__(self):
        self.prov = None

    def translate(self, data, *args, **kwargs):
        raise NotImplementedError()

    def clean(self):
        # NOTE: unification removes duplicates by deleting multiplicities with same identifier
        # can also be used to remove duplicated relations, iff relation has identifier
        if not isinstance(self.prov, pm.ProvDocument):
            raise TypeError
        self.prov = self.prov.unified()


class CommitTranslator(Translator):

    def __init__(self):
        super().__init__()

    def translate(self, commits, *args, **kwargs):
        # document setup
        prov = pm.ProvDocument()
        prov.set_default_namespace("https://example.org")

        # compute lookups: somewhat memory intensive, maybe cut off waste?
        al = self._compute_alias_lookup(commits)
        cl = self._compute_commit_lookup(commits)

        for commit in cl.values():
            nmsp = self._format_names(commit)
            prov.activity(
                    identifier=nmsp.commit,
                    other_attributes={PROV_LABEL: commit.message})
            prov.wasStartedBy(
                    nmsp.commit,
                    time=commit.authored_date,
                    identifier=nmsp.commit+commit.authored_date)
            prov.wasEndedBy(
                    nmsp.commit,
                    time=commit.committed_date,
                    identifier=nmsp.commit+commit.committed_date)

        for commit in commits:
            nmsp = self._format_names(commit)
            for parent in nmsp.parents:
                prov.wasInformedBy(
                        nmsp.commit,
                        parent,
                        identifier=nmsp.commit+parent)
            prov.agent(identifier=nmsp.author)
            prov.agent(identifier=nmsp.committer)
            prov.wasAssociatedWith(
                    nmsp.commit,
                    nmsp.author,
                    other_attributes={PROV_ROLE: "author"})
            prov.wasAssociatedWith(
                    nmsp.commit,
                    nmsp.committer,
                    other_attributes={PROV_ROLE: "committer"})

            used_files = self._search_used_versions(al, cl, commit)
            if commit.file_action == FileAction.DELETED:
                for cid in used_files:
                    prov.wasInvalidatedBy(
                            f"file-{self._namify(cl[cid].generated)}_commit-{cid}",
                            nmsp.commit,
                            time=commit.authored_date)
            else:
                prov.entity(identifier=nmsp.generated)
                prov.wasAttributedTo(nmsp.generated, nmsp.author)
                stem_file = al[commit.used]
                prov.specializationOf(
                        nmsp.generated,
                        f"file-{self._namify(stem_file)}")
                prov.wasGeneratedBy(
                        nmsp.generated,
                        nmsp.commit,
                        time=commit.authored_date)
            if commit.file_action == FileAction.ADDED:
                prov.entity(
                        nmsp.file,
                        other_attributes={PROV_LABEL: commit.used})
            if commit.file_action == FileAction.MODIFIED:
                for cid in used_files:
                    prov.used(
                            nmsp.commit,
                            f"file-{self._namify(cl[cid].generated)}_commit-{cid}",
                            time=commit.authored_date)
                    prov.wasDerivedFrom(
                            nmsp.generated,
                            f"file-{self._namify(cl[cid].generated)}_commit-{cid}",
                            nmsp.commit)
        self.prov = prov

    def _compute_commit_lookup(self, commits):
        cl = dict()
        for commit in commits:
            if not cl.get(commit.id, False):
                commit.files = [(commit.used, commit.generated)]
                cl[commit.id] = commit
                continue
            origin = cl.get(commit.id)
            if not hasattr(origin, "files"):
                origin.files = [(origin.used, origin.generated)]
            origin.files.append((commit.used, commit.generated))
            cl[commit.id] = origin
        return cl

    def _search_used_versions(self, al, cl, c):
        # TODO: i don't think this is robust yet.
        # The following case yields a wrong result searching for F
        #        * -- F
        #        |
        #      /  \
        #     /    *--F'
        # G--*     |
        #    \     |
        #     \   /
        #      \ /
        #       *
        # RESULT: F, F'
        stack, visited = [c.id], []
        res = []
        if c.file_action == FileAction.ADDED:
            return []
        while stack:
            active = stack.pop()
            if active in visited:
                continue
            visited.append(active)
            for _, gen in cl.get(active).files:
                if active != c.id and al[gen] == al[c.used]:
                    res.append(active)
                    break
            else:
                for parent in cl[active].parent_ids:
                    stack.append(parent)
        return res

    def _namify(self, string):
        replacements = {"-": ["/", ".", " "]}
        for rep, sublist in replacements.items():
            for sub in sublist:
                string = string.replace(sub, rep)
        return string

    def _format_names(self, commit):
        namespace = "commit parents author committer file generated"
        Names = namedtuple("Names", namespace)
        return Names(*[
            f"commit-{commit.id}",
            [f"commit-{pid}" for pid in commit.parent_ids],
            f"user-{self._namify(commit.author_name)}",
            f"user-{self._namify(commit.committer_name)}",
            f"file-{self._namify(commit.used)}",
            f"file-{self._namify(commit.generated)}_commit-{commit.id}"])

    def _compute_alias_lookup(self, commits):
        track = defaultdict(set)  # file alias records
        files = set()  # list of filenames
        for commit in commits:
            files |= set([commit.used, commit.generated])
            track[commit.used].add(commit.generated)

        # explore file records by bfs to compute file tracks
        roots = []
        for f in files:
            queue, visited = deque([f]), list()
            while queue:
                active = queue.popleft()
                visited.append(active)
                for node in track.get(active, []):
                    if node in visited:
                        continue
                    queue.append(node)
            roots.append(visited)

        # compute lookup for root file names
        lookup = dict()
        for f in files:
            track = sorted(filter(lambda l: f in l, roots), key=len)[-1]
            root, *n = track
            lookup[root] = root
            for child in n:
                lookup[child] = root
        return lookup
