import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("file")
document.entity("file_v-1")
document.entity("file_v")
document.activity("parent_commit")
document.activity("gitlab_commit")
document.agent("author")
document.agent("committer")

# Relations
document.wasInvalidatedBy("file_v", "gitlab_commit")
document.wasInformedBy("gitlab_commit", "parent_commit")
document.specializationOf("file_v", "file")
document.specializationOf("file_v-1", "file")
document.wasDerivedFrom("file_v", "file_v-1")
document.wasAssociatedWith("gitlab_commit", "author")
document.wasAssociatedWith("gitlab_commit", "committer")
document.wasAttributedTo("file_v", "author")

COMMIT_MODEL_DELETE = document
