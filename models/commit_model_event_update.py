import prov.model


document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")

# Nodes
document.entity("commit")
document.entity("commit_v-1")
document.entity("commit_v")
document.activity("previous_event")
document.activity("commit_event")
document.agent("eventee")

# Relations
document.used("commit_event", "commit_v-1")
document.wasGeneratedBy("commit_v", "commit_event")
document.wasDerivedFrom("commit_v", "commit_v-1")
document.specializationOf("commit_v", "commit")
document.specializationOf("commit_v-1", "commit")
document.wasInformedBy("commit_event", "previous_event")
document.wasAssociatedWith("commit_event", "eventee")
document.wasAttributedTo("commit_v", "eventee")

COMMIT_MODEL_EVENT_UPDATE = document
