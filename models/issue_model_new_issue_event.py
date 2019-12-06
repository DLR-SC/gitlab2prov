import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("issue")
document.entity("issue_v-1")
document.entity("issue_v")
document.activity("issue_event")
document.activity("previous_event")
document.agent("gitlab_event_initiator")

# Relations
document.used("issue_event", "issue_v-1")
document.wasGeneratedBy("issue_v", "issue_event")
document.wasDerivedFrom("issue_v", "issue_v-1")
document.specializationOf("issue_v", "issue")
document.specializationOf("issue_v-1", "issue")
document.wasInformedBy("issue_event", "previous_event")
document.wasAssociatedWith("issue_event", "gitlab_event_initiator")
document.wasAttributedTo("issue_v", "gitlab_event_initiator")

ISSUE_MODEL_NEW_ISSUE_EVENT = document
