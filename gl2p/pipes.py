from copy import deepcopy
from urllib.parse import urlparse
from gitlab import Gitlab
from gl2p.translators import CommitTranslator
from gl2p.commons import FileAction


class Pipeline:
    def __init__(self, config):
        self._config = config
        self.gitlab_api = None
        self.project = None
        self.translator = None

        self._init_gitlab_api()
        self._init_project()

    def _init_gitlab_api(self):
        self.gitlab_api = Gitlab(
                url=self._config["GITLAB"]["url"], 
                private_token=self._config["GITLAB"]["token"])

    def _init_project(self):
        project_path = self._pathify(self._config["GITLAB"]["project"])
        self.project = self.gitlab_api.projects.get(project_path)

    def _pathify(self, url):
        # NOTE: remove leading slash
        return urlparse(url).path.replace("/", "", 1)
    
    def request_data(self, *args, **kwargs):
        raise NotImplementedError()

    def translate_data(self, *args, **kwargs):
        raise NotImplementedError()

    def commit_data(self, *args, **kwargs):
        raise NotImplementedError()


class CommitPipeline(Pipeline):

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.translator = CommitTranslator()
        self.commits = None

    def request_data(self):
        # NOTE: reverse order to sort ascending by date
        self.commits = list(reversed(self.project.commits.list(all=True)))

        # TODO: asynchronous fetching of diffs
        # Synchronous is time consuming for large repositories.
        # Also, linear growth of waiting time is not fun.
        # Example:
        # Repository of 20,000 commits
        # - request the diff for each commit: 20,000 requests
        # - waiting time: 20,000 * 0,3sec = 6000sec = 100min
        # Assuming avg response in 0,3sec and synchronous execution

        for n, commit in enumerate(self.commits):
            diff = commit.diff()
            updated = []
            for entry in diff:
                copy = deepcopy(commit)
                copy.file_path_used = entry["old_path"]
                copy.file_path_generated = entry["new_path"]
                copy.file_action = self._get_file_action(entry)
                updated.append(copy)
            self.commits[n] = updated
        self.commits = [c for clist in self.commits for c in clist]

    def translate_data(self, *args, **kwargs):
        self.translator.translate(self.commits)

    def commit_data(self, *args, **kwargs):
        self.translator.clean()
        translation = self.translator.prov
        return translation

    def _get_file_action(self, entry):
        if entry["new_file"]:
            return FileAction.ADDED
        elif entry["deleted_file"]:
            return FileAction.DELETED
        return FileAction.MODIFIED
