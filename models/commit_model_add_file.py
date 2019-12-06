import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("file")
document.entity("file_version")
document.agent("author")
document.agent("committer")
document.activity("gitlab_commit")
document.activity("parent_commit")

# Relations
document.wasAttributedTo("file", "author")
document.wasAttributedTo("file_version", "author")
document.wasGeneratedBy("file", "gitlab_commit")
document.wasGeneratedBy("file_version", "gitlab_commit")
document.wasAssociatedWith("gitlab_commit", "author")
document.wasAssociatedWith("gitlab_commit", "committer")
document.specializationOf("file_version", "file")
document.wasInformedBy("gitlab_commit", "parent_commit")

COMMIT_MODEL_ADD_FILE = document
