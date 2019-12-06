import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("issue")
document.entity("issue_version")
document.activity("issue_event")
document.activity("commit")
document.agent("gitlab_issue_opener")

# Relations
document.wasGeneratedBy("issue", "issue_event")
document.wasGeneratedBy("issue_version", "issue_event")
document.specializationOf("issue_version", "issue")
document.wasAttributedTo("issue_version", "gitlab_issue_opener")
document.wasAttributedTo("issue", "gitlab_issue_opener")
document.wasInformedBy("issue_event", "commit")
document.wasAssociatedWith("issue_event", "gitlab_issue_opener")

ISSUE_MODEL_NEW_ISSUE = document
