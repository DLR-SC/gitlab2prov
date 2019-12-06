import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("file")
document.entity("file_v-1")
document.entity("file_v")
document.activity("gitlab_commit")
document.activity("parent_commit")
document.agent("author")
document.agent("committer")

# Relations
document.wasInformedBy("gitlab_commit", "parent_commit")
document.wasGeneratedBy("file_v", "gitlab_commit")
document.used("gitlab_commit", "file_v-1")
document.wasDerivedFrom("file_v", "file_v-1")
document.specializationOf("file_v", "file")
document.specializationOf("file_v-1", "file")
document.wasAttributedTo("file_v", "author")
document.wasAssociatedWith("gitlab_commit", "author")
document.wasAssociatedWith("gitlab_commit", "committer")

COMMIT_MODEL_MODIFY = document
