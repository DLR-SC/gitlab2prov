import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("previous_issue")
document.entity("issue_version_annotation")

# Relations
document.alternateOf("issue_version_annotation", "previous_issue")

ISSUE_MODEL_MARKED_AS_DUPLICATE = document
