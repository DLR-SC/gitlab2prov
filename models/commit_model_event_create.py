import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("commit")
document.entity("commit_version")
document.activity("gitlab_commit")
document.activity("parent_commit")
document.agent("committer")

# Relations
document.wasInformedBy("gitlab_commit", "parent_commit")
document.wasGeneratedBy("commit", "gitlab_commit")
document.wasGeneratedBy("commit_version", "gitlab_commit")
document.specializationOf("commit_version", "commit")
document.wasAssociatedWith("gitlab_commit", "committer")
document.wasAttributedTo("commit", "committer")
document.wasAttributedTo("commit_version", "committer")

COMMIT_MODEL_EVENT_CREATE = document
