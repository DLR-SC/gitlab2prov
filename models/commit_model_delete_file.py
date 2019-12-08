import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("file")
document.entity("file_v-1")
document.activity("parent_commit")
document.activity("gitlab_commit")
document.agent("author")
document.agent("committer")

# Relations
document.wasInvalidatedBy("file_v-1", "gitlab_commit")
document.wasGeneratedBy("file_v-1", "parent_commit")
document.wasInformedBy("gitlab_commit", "parent_commit")
document.specializationOf("file_v-1", "file")
document.wasAssociatedWith("gitlab_commit", "author")
document.wasAssociatedWith("gitlab_commit", "committer")

COMMIT_MODEL_DELETE_FILE = document
