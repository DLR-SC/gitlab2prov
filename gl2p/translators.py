from collections import defaultdict, deque
import prov.model as pm
from prov.constants import PROV_LABEL, PROV_ROLE
from gl2p.commons import FileAction
from gl2p.config import CONFIG
from urllib.parse import urlparse


class Translator:

    def __init__(self, data=None):
        self.prov = None
        self.data = data

    def translate(self, data, *args, **kwargs):
        raise NotImplementedError()

    def clean(self):
        if not isinstance(self.prov, pm.ProvDocument):
            raise TypeError
        self.prov = self.prov.unified()


class CommitTranslator(Translator):

    def __init__(self, data=None):
        super().__init__(data)
        self.commit_lookup = self._cmpt_commit_lookup()
        self.alias_lookup = self._cmpt_alias_lookup()
    
    def translate(self, *args, **kwargs):
        # init prov document
        prov = pm.ProvDocument()
        
        prov.set_default_namespace("gl2p")
        api_url = "://".join(urlparse(CONFIG["GITLAB"]["url"])[:2]) + "/api/v4/"
        prov.add_namespace("gitlab", api_url)
        # prov.set_default_namespace("https://example.org")
        bundle = prov.bundle("gl2p:CommitModel")

        # for each commit do only once
        # commit centric view
        for cid in set(c.id for c in self.data):
            commit = self.commit_lookup[cid]
            self._add_activities(commit, bundle)
            self._add_activity_time_relations(commit, bundle)
            self._add_activity_parenting_relations(commit, bundle)
            self._add_agent_associations(commit, bundle)
            self._add_agents(commit, bundle)

        # for each file action once, file centric view
        for commit in self.data:
            self._add_file_action_dependees(commit, bundle)

        # add gitlab commit resolvables
        for cid in set(c.id for c in self.data):
            commit = self.commit_lookup[cid]
            self._add_resolvables(commit, bundle)
        self.prov = prov

    def _add_activities(self, commit, prov_obj):
        cmt_name = "commit-{}".format(commit.id)
        prov_obj.activity(
                identifier=cmt_name,
                other_attributes={PROV_LABEL: commit.message})

    def _add_activity_time_relations(self, commit, prov_obj):
        cmt_name = "commit-{}".format(commit.id)
        prov_obj.wasStartedBy(
                activity=cmt_name,
                time=commit.authored_date,
                identifier=cmt_name+commit.authored_date)
        prov_obj.wasEndedBy(
                activity=cmt_name,
                time=commit.committed_date,
                identifier=cmt_name+commit.committed_date)

    def _add_activity_parenting_relations(self, commit, prov_obj):
        cmt_name = "commit-{}".format(commit.id)
        for parent in commit.parent_ids:
            parent = "commit-{}".format(parent)
            prov_obj.wasInformedBy(
                    informed=cmt_name,
                    informant=parent,
                    identifier=cmt_name + "_" + parent)

    def _add_agent_associations(self, commit, prov_obj):
        cmt_name = "commit-{}".format(commit.id)
        committer = "user-{}".format(self._namify(commit.committer_name))
        author = "user-{}".format(self._namify(commit.author_name))
        prov_obj.wasAssociatedWith(
                activity=cmt_name,
                agent=author,
                identifier=f"author-{cmt_name}",
                other_attributes={PROV_ROLE: "author"})
        prov_obj.wasAssociatedWith(
                activity=cmt_name,
                agent=committer,
                identifier=f"committer-{cmt_name}",
                other_attributes={PROV_ROLE: "committer"})

    def _add_agents(self, commit, prov_obj):
        author = "user-{}".format(self._namify(commit.author_name))
        committer = "user-{}".format(self._namify(commit.committer_name))
        prov_obj.agent(identifier=author)
        prov_obj.agent(identifier=committer)

    def _add_file_action_deleted(self, commit, prov_obj):
        for version_id in self._used_versions(commit):
            if not self.commit_lookup.get(version_id):
                continue
            file_name = self._namify(self.commit_lookup[version_id].generated)
            entity_identifier = "file-{}_commit-{}".format(file_name, version_id)
            prov_obj.wasInvalidatedBy(
                    entity=entity_identifier,
                    activity="commit-{}".format(commit.id), 
                    time=commit.authored_date)

    def _add_file_action_added(self, commit, prov_obj):
        identifier = "file-{}".format(self._namify(commit.used))
        prov_obj.entity(
                identifier=identifier,
                other_attributes={PROV_LABEL: commit.used})

    def _add_file_action_default(self, commit, prov_obj):
        generated = "file-{}_commit-{}".format(self._namify(commit.generated), commit.id)
        agent = "user-{}".format(self._namify(commit.author_name))
        prov_obj.entity(identifier=generated)
        prov_obj.wasAttributedTo(entity=generated, agent=agent)
        prov_obj.wasGeneratedBy(
                entity=generated,
                activity="commit-{}".format(commit.id),
                time=commit.authored_date)
        # find stem file that gets added
        origin = self.alias_lookup[commit.used]
        prov_obj.specializationOf(
                specificEntity=generated,
                generalEntity="file-{}".format(self._namify(origin)))

    def _add_file_action_dependees(self, commit, prov_obj):
        # default prov voc to add
        if commit.file_action != FileAction.DELETED:
            self._add_file_action_default(commit, prov_obj)
        if commit.file_action == FileAction.ADDED:
            self._add_file_action_added(commit, prov_obj)
            return
        if commit.file_action == FileAction.MODIFIED:
            self._add_file_action_modified(commit, prov_obj)
            return
        self._add_file_action_deleted(commit, prov_obj)
        self._add_resolvables(commit, prov_obj)

    def _add_file_action_modified(self, commit, prov_obj):
        gen = "file-{}_commit-{}".format(self._namify(commit.generated), commit.id)
        for version_id in self._used_versions(commit):
            if not self.commit_lookup.get(version_id):
                continue
            file_name = self._namify(self.commit_lookup[version_id].generated)
            file_version = "file-{}_commit-{}".format(file_name, version_id)
            prov_obj.used(
                    activity="commit-{}".format(commit.id),
                    entity=file_version,
                    time=commit.authored_date)
            prov_obj.wasDerivedFrom(
                    generatedEntity=gen,
                    usedEntity=file_version,
                    activity="commit-{}".format(commit.id))

    def _add_resolvables(self, commit, prov_obj):
        # namespace prefix: gitlab
        project = urlparse(CONFIG["GITLAB"]["project"]).path.replace("/","", 1).replace("/", "%2F")
        commit_res = "projects/" + project + "/repository/commits/" + commit.id
        print(project)
        print(commit_res)
        prov_obj.activity(identifier="gitlab:" + commit_res)

        # connect to commit ressource from commit model
        prov_obj.wasInformedBy(informed="gitlab:" + commit_res, informant=f"commit-{commit.id}")

        # For each parent wasInformedBy Relation
        for pid in commit.parent_ids:
            informant = f"commit-{pid}"
            prov_obj.wasInformedBy(informed="gitlab:"+commit_res, informant=informant)

        # wasAssociatedWith relation to GitLab committer
        # user url
        #user_res = "users/:id"
        #prov_obj.agent(identifier="gitlab-committer", other_attributes={"url"})
        #prov_obj.wasAssociatedWith(activity="gitlab:"+commit_res, agent="gitlab:"+user_res)

    def _cmpt_commit_lookup(self):
        # problem when history is inconsistent
        cl = dict()
        for commit in self.data:
            if commit.id not in cl:
                commit.files = [(commit.used, commit.generated)]
                cl[commit.id] = commit
                continue
            origin = cl.get(commit.id)
            if not hasattr(origin, "files"):
                origin.files = [(origin.used, origin.generated)]
            origin.files.append((commit.used, commit.generated))
            cl[commit.id] = origin
        return cl

    def _used_versions(self, commit):
        # file versioning by assigning parent commits as versions
        return [pid for pid in commit.parent_ids]

    def _search_used_versions(self, c):
        # revert back to simple version tracking
        # problem when history is inconsistent
        # TODO: i don't think this is robust yet.
        stack, visited, res = [c.id], list(), list()
        if c.file_action == FileAction.ADDED:
            return []
        while stack:
            active = stack.pop()
            # print("ACTIVE", active)
            # print(self.commit_lookup.keys())
            if active in visited:
                continue
            visited.append(active)
            for _, gen in self.commit_lookup.get(active).files:
                if (self.alias_lookup[gen] == self.alias_lookup[c.used]
                        and active != c.id):
                    res.append(active)
                    break
            else:
                for parent in self.commit_lookup[active].parent_ids:
                    stack.append(parent)
        return res

    def _namify(self, string):
        replacements = {"-": ["/", ".", " "]}
        for rep, sublist in replacements.items():
            for sub in sublist:
                string = string.replace(sub, rep)
        return string

    def _cmpt_alias_lookup(self):
        track, files = defaultdict(set), set()  # file alias records
        for commit in self.data:
            files |= set([commit.used, commit.generated])
            track[commit.used].add(commit.generated)

        roots = []  # explore file records by bfs to compute file tracks
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

        lookup = dict()
        for f in files:
            track = sorted(filter(lambda l: f in l, roots), key=len)[-1]
            root, *n = track
            lookup[root] = root
            for child in n:
                lookup[child] = root
        return lookup
