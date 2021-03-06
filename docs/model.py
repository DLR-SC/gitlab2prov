from prov.model import ProvDocument
from prov.constants import PROV_LABEL
from prov.dot import prov_to_dot


add = ProvDocument()
add.set_default_namespace("gitlab2prov:")
add.activity("Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""})
add.activity("Parent Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""})
add.agent("Committer", other_attributes={"prov:type": "user", "prov:role": "committer", "name": "", "email": ""})
add.agent("Author", other_attributes={"prov:type": "user", "prov:role": "author", "name": "", "email": ""})
add.entity("File", other_attributes={"prov:type": "file", "path_at_addition": ""})
add.entity("File Version", other_attributes={"prov:type": "file_version", "old_path": "", "new_path": ""})
add.wasInformedBy("Commit", "Parent Commit")
add.wasAssociatedWith("Commit", "Committer")
add.wasAssociatedWith("Commit", "Author")
add.wasGeneratedBy("File", "Commit")
add.wasGeneratedBy("File Version", "Commit")
add.wasAttributedTo("File", "Author")
add.wasAttributedTo("File Version", "Author")
add.specializationOf("File Version", "File")


mod = ProvDocument()
mod.set_default_namespace("gitlab2prov:")
mod.activity("Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""},)
mod.activity("Parent Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""},)
mod.agent("Committer", other_attributes={"prov:type": "user", "prov:role": "committer", "name": "", "email": ""})
mod.agent("Author", other_attributes={"prov:type": "user", "prov:role": "author", "name": "", "email": "",})
mod.entity("File", other_attributes={"prov:type": "file", "path_at_addition": ""})
mod.entity("File Version N", other_attributes={"prov:type": "file_version", "new_path": "", "old_path": ""})
mod.entity("File Version N-1", other_attributes={"prov:type": "file_version", "new_path": "", "old_path": ""})
mod.wasInformedBy("Commit", "Parent Commit")
mod.wasAssociatedWith("Commit", "Author")
mod.wasAssociatedWith("Commit", "Committer")
mod.used("Commit", "File Version N-1")
mod.wasGeneratedBy("File Version N", "Commit")
mod.wasDerivedFrom("File Version N", "File Version N-1")
mod.specializationOf("File Version N", "File")
mod.specializationOf("File Version N-1", "File")
mod.wasAttributedTo("File Version N", "Author")


rem = ProvDocument()
rem.set_default_namespace("gitlab2prov:")
rem.activity("Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""})
rem.activity("Parent Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""})
rem.agent("Committer", other_attributes={"prov:type": "user", "prov:role": "committer", "name": "", "email": ""})
rem.agent("Author", other_attributes={"prov:type": "user", "prov:role": "author", "name": "", "email": ""})
rem.entity("File", other_attributes={"prov:type": "file", "path_at_addition": ""})
rem.entity("File Version", other_attributes={"prov:type": "file_version", "new_path": "", "old_path": ""})
rem.wasInformedBy("Commit", "Parent Commit")
rem.wasAssociatedWith("Commit", "Committer")
rem.wasAssociatedWith("Commit", "Author")
rem.wasInvalidatedBy("File Version", "Commit")
rem.specializationOf("File Version", "File")


com = ProvDocument()
com.set_default_namespace("gitlab2prov:")
com.agent("Creator", other_attributes={"prov:type": "user", "prov:role": "creator", "name": ""})
com.agent("Annotator", other_attributes={"prov:type": "user", "prov:role": "initiator", "name": ""})
com.activity("Commit Creation", other_attributes={"prov:type": "creation", "prov:startedAt": "", "prov:endedAt": ""})
com.activity("Commit Annotation", other_attributes={"prov:type": "event", "prov:startedAt": "", "prov:endedAt": "", "event": ""})
com.activity("Git Commit", other_attributes={"prov:type": "commit", "title": "", "message": "", "id": "", "short_id": "", "prov:startedAt": "", "prov:endedAt": ""})
com.wasInformedBy("Commit Creation", "Git Commit")
com.entity("Commit", other_attributes={"prov:type": "commit_resource", "title": "", "message": "", "short_id": "", "id": ""})
com.entity("Commit Version", other_attributes={"prov:type": "commit_resource_version"})
com.entity("Annotated Commit Version", other_attributes={"prov:type": "commit_resource_version"},)
com.wasAssociatedWith("Commit Creation", "Creator")
com.wasAttributedTo("Commit", "Creator")
com.wasAttributedTo("Commit Version", "Creator")
com.wasGeneratedBy("Commit", "Commit Creation")
com.wasGeneratedBy("Commit Version", "Commit Creation")
com.wasAttributedTo("Annotated Commit Version", "Annotator")
com.wasAssociatedWith("Commit Annotation", "Annotator")
com.used("Commit Annotation", "Commit Version")
com.wasInformedBy("Commit Annotation", "Commit Creation")
com.wasGeneratedBy("Annotated Commit Version", "Commit Annotation")
com.specializationOf("Commit Version", "Commit")
com.specializationOf("Annotated Commit Version", "Commit")
com.wasDerivedFrom("Annotated Commit Version", "Commit Version")


mr = ProvDocument()
mr.set_default_namespace("gitlab2prov:")
mr.agent("Creator", other_attributes={"prov:type": "user", "prov:role": "creator", "name": ""},)
mr.agent("Annotator", other_attributes={"prov:type": "user", "prov:role": "initiator", "name": ""})
mr.activity("Merge Request Creation", other_attributes={"prov:type": "merge_request_creation", "prov:startedAt": "", "prov:endedAt": ""})
mr.activity("Merge Request Annotation", other_attributes={"prov:type": "event", "prov:startedAt": "", "prov:endedAt": "", "event": ""})
mr.entity("Merge Request", other_attributes={"prov:type": "merge_request_resource", "id": "", "iid": "", "title": "", "description": "", "web_url": "", "project_id": "", "source_branch": "", "target_branch": "", "source_project_url": "", "target_project_url": ""})
mr.entity("Merge Request Version", other_attributes={"prov:type": "merge_request_resource_version"},)
mr.entity("Annotated Merge Request Version", other_attributes={"prov:type": "merge_request_resource_version"},)
mr.wasInformedBy("Merge Request Annotation", "Merge Request Creation")
mr.wasGeneratedBy("Merge Request", "Merge Request Creation")
mr.wasGeneratedBy("Merge Request Version", "Merge Request Creation")
mr.wasGeneratedBy("Annotated Merge Request Version", "Merge Request Annotation")
mr.used("Merge Request Annotation", "Merge Request Version")
mr.specializationOf("Merge Request Version", "Merge Request")
mr.specializationOf("Annotated Merge Request Version", "Merge Request")
mr.wasDerivedFrom("Annotated Merge Request Version", "Merge Request Version")
mr.wasAttributedTo("Annotated Merge Request Version", "Annotator")
mr.wasAttributedTo("Merge Request Version", "Creator")
mr.wasAttributedTo("Merge Request", "Creator")
mr.wasAssociatedWith("Merge Request Creation", "Creator")
mr.wasAssociatedWith("Merge Request Annotation", "Annotator")


iss = ProvDocument()
iss.set_default_namespace("gitlab2prov:")
iss.agent("Creator", other_attributes={"prov:type": "user", "prov:role": "creator", "name": ""})
iss.agent("Annotator", other_attributes={"prov:type": "user", "prov:role": "initiator", "name": ""})
iss.activity("Issue Creation", other_attributes={"prov:type": "issue_creation", "prov:startedAt": "", "prov:endedAt": ""})
iss.activity("Issue Annotation", other_attributes={"prov:type": "event", "prov:startedAt": "", "prov:endedAt": "", "event": ""})
iss.entity("Issue", other_attributes={"prov:type": "issue_resource", "id": "", "iid": "", "title": "", "description": "", "project_id": "", "web_url": ""})
iss.entity("Issue Version", other_attributes={"prov:type": "issue_resource_version"})
iss.entity("Annotated Issue Version", other_attributes={"prov:type": "issue_resource_version"})
iss.wasInformedBy("Issue Annotation", "Issue Creation")
iss.wasGeneratedBy("Issue", "Issue Creation")
iss.wasGeneratedBy("Issue Version", "Issue Creation")
iss.wasGeneratedBy("Annotated Issue Version", "Issue Annotation")
iss.used("Issue Annotation", "Issue Version")
iss.specializationOf("Issue Version", "Issue")
iss.specializationOf("Annotated Issue Version", "Issue")
iss.wasDerivedFrom("Annotated Issue Version", "Issue Version")
iss.wasAttributedTo("Annotated Issue Version", "Annotator")
iss.wasAttributedTo("Issue Version", "Creator")
iss.wasAttributedTo("Issue", "Creator")
iss.wasAssociatedWith("Issue Creation", "Creator")
iss.wasAssociatedWith("Issue Annotation", "Annotator")


for title, doc in [
    ("git_commit_model_add", add),
    ("git_commit_model_mod", mod),
    ("git_commit_model_del", rem),
    ("gitlab_commit_model", com),
    ("gitlab_issue_model", iss),
    ("gitlab_merge_request_model", mr),
]:
    prov_to_dot(doc, show_nary=False, use_labels=False, direction="BT").write_pdf(
        f"pdfs/{title}.pdf"
    )
    prov_to_dot(doc, show_nary=False, use_labels=False, direction="BT").write_svg(
        f"svgs/{title}.svg"
    )
