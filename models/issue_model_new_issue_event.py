import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("issue")
document.entity("issue_version")
document.entity("issue_version_annotation")
document.activity("issue_event_annotation")
document.activity("annotator_commit")
document.agent("gitlab_annotator")

# Relations
document.used("issue_event_annotation", "issue_version")
document.wasGeneratedBy("issue_version_annotation", "issue_event_annotation")
document.wasDerivedFrom("issue_version_annotation", "issue_version")
document.specializationOf("issue_version_annotation", "issue")
document.specializationOf("issue_version", "issue")
document.wasInformedBy("issue_event_annotation", "annotator_commit")
document.wasAssociatedWith("issue_event_annotation", "gitlab_annotator")
document.wasAttributedTo("issue_version_annotation", "gitlab_annotator")

ISSUE_MODEL_NEW_ISSUE_EVENT = document
