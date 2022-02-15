"""PROV model fpr GitLab2PROV."""

__author__ = "Claas de Boer, Andreas Schreiber, Lynn von Kurnatowski"
__copyright__ = "Copyright 2020, German Aerospace Center (DLR) and individual contributors"
__license__ = "MIT"
__version__ = "1.0"
__status__ = "Stable"


from prov.model import ProvDocument
from prov.dot import prov_to_dot


add = ProvDocument()
add.set_default_namespace("gitlab2prov:")
add.activity("Commit")
add.activity("Parent Commit")
add.agent("Committer")
add.agent("Author")
add.entity("File")
add.entity("File Revision")
add.wasInformedBy("Commit", "Parent Commit")
add.wasAssociatedWith("Commit", "Committer")
add.wasAssociatedWith("Commit", "Author")
add.wasGeneratedBy("File", "Commit")
add.wasGeneratedBy("File Revision", "Commit")
add.wasAttributedTo("File", "Author")
add.wasAttributedTo("File Revision", "Author")
add.specializationOf("File Revision", "File")


mod = ProvDocument()
mod.set_default_namespace("gitlab2prov:")
mod.activity("Commit")
mod.activity("Parent Commit")
mod.agent("Committer")
mod.agent("Author")
mod.entity("File")
mod.entity("File Revision")
mod.entity("Previous File Revision")
mod.wasInformedBy("Commit", "Parent Commit")
mod.wasAssociatedWith("Commit", "Author")
mod.wasAssociatedWith("Commit", "Committer")
mod.used("Commit", "Previous File Revision")
mod.wasGeneratedBy("File Revision", "Commit")
mod.wasRevisionOf("File Revision", "Previous File Revision")
mod.specializationOf("File Revision", "File")
mod.specializationOf("Previous File Revision", "File")
mod.wasAttributedTo("File Revision", "Author")


rem = ProvDocument()
rem.set_default_namespace("gitlab2prov:")
rem.activity("Commit")
rem.activity("Parent Commit")
rem.agent("Committer")
rem.agent("Author")
rem.entity("File")
rem.entity("File Revision")
rem.wasInformedBy("Commit", "Parent Commit")
rem.wasAssociatedWith("Commit", "Committer")
rem.wasAssociatedWith("Commit", "Author")
rem.wasInvalidatedBy("File Revision", "Commit")
rem.specializationOf("File Revision", "File")


com = ProvDocument()
com.set_default_namespace("gitlab2prov:")
com.agent("Gitlab Commit Author")
com.agent("Annotator")
com.activity("Creation")
com.activity("Annotation")
com.activity("Git Commit")
com.wasInformedBy("Creation", "Git Commit")
com.entity("Commit")
com.entity("Commit Version")
com.entity("Annotated Commit Version")
com.wasAssociatedWith("Creation", "Gitlab Commit Author")
com.wasAttributedTo("Commit", "Gitlab Commit Author")
com.wasAttributedTo("Commit Version", "Gitlab Commit Author")
com.wasGeneratedBy("Commit", "Creation")
com.wasGeneratedBy("Commit Version", "Creation")
com.wasAttributedTo("Annotated Commit Version", "Annotator")
com.wasAssociatedWith("Annotation", "Annotator")
com.used("Annotation", "Commit Version")
com.wasInformedBy("Annotation", "Creation")
com.wasGeneratedBy("Annotated Commit Version", "Annotation")
com.specializationOf("Commit Version", "Commit")
com.specializationOf("Annotated Commit Version", "Commit")
com.wasDerivedFrom("Annotated Commit Version", "Commit Version")


mr = ProvDocument()
mr.set_default_namespace("gitlab2prov:")
mr.agent("Merge Request Author")
mr.agent("Annotator")
mr.activity("Creation")
mr.activity("Annotation")
mr.entity("Merge Request")
mr.entity("Merge Request Version")
mr.entity("Annotated Merge Request Version")
mr.wasInformedBy("Annotation", "Creation")
mr.wasGeneratedBy("Merge Request", "Creation")
mr.wasGeneratedBy("Merge Request Version", "Creation")
mr.wasGeneratedBy("Annotated Merge Request Version", "Annotation")
mr.used("Annotation", "Merge Request Version")
mr.specializationOf("Merge Request Version", "Merge Request")
mr.specializationOf("Annotated Merge Request Version", "Merge Request")
mr.wasDerivedFrom("Annotated Merge Request Version", "Merge Request Version")
mr.wasAttributedTo("Annotated Merge Request Version", "Annotator")
mr.wasAttributedTo("Merge Request Version", "Merge Request Author")
mr.wasAttributedTo("Merge Request", "Merge Request Author")
mr.wasAssociatedWith("Creation", "Merge Request Author")
mr.wasAssociatedWith("Annotation", "Annotator")


iss = ProvDocument()
iss.set_default_namespace("gitlab2prov:")
iss.agent("Issue Author")
iss.agent("Annotator")
iss.activity("Creation")
iss.activity("Annotation")
iss.entity("Issue")
iss.entity("Issue Version")
iss.entity("Annotated Issue Version")
iss.wasInformedBy("Annotation", "Creation")
iss.wasGeneratedBy("Issue", "Creation")
iss.wasGeneratedBy("Issue Version", "Creation")
iss.wasGeneratedBy("Annotated Issue Version", "Annotation")
iss.used("Annotation", "Issue Version")
iss.specializationOf("Issue Version", "Issue")
iss.specializationOf("Annotated Issue Version", "Issue")
iss.wasDerivedFrom("Annotated Issue Version", "Issue Version")
iss.wasAttributedTo("Annotated Issue Version", "Annotator")
iss.wasAttributedTo("Issue Version", "Issue Author")
iss.wasAttributedTo("Issue", "Issue Author")
iss.wasAssociatedWith("Creation", "Issue Author")
iss.wasAssociatedWith("Annotation", "Annotator")


release_tag_model = ProvDocument()
release_tag_model.set_default_namespace("gitlab2prov:")
release_tag_model.agent("Release Author")
release_tag_model.agent("Tag Author")
release_tag_model.agent("Author")

release_tag_model.activity("Release Creation")
release_tag_model.activity("Tag Creation")
release_tag_model.activity("Commit Creation")
release_tag_model.entity("Tag")
release_tag_model.entity("Release")
release_tag_model.entity("Commit")
release_tag_model.entity("Evidence")
release_tag_model.entity("Asset")
release_tag_model.hadMember("Asset", "Release")
release_tag_model.hadMember("Evidence", "Release")
release_tag_model.hadMember("Tag", "Release")
release_tag_model.hadMember("Commit", "Tag")
release_tag_model.wasAssociatedWith("Commit Creation", "Author")
release_tag_model.wasAssociatedWith("Release Creation", "Release Author")
release_tag_model.wasAssociatedWith("Tag Creation", "Tag Author")
release_tag_model.wasAttributedTo("Release", "Release Author")
release_tag_model.wasAttributedTo("Tag", "Tag Author")
release_tag_model.wasAttributedTo("Commit", "Author")
release_tag_model.wasGeneratedBy("Release", "Release Creation")
release_tag_model.wasGeneratedBy("Tag", "Tag Creation")
release_tag_model.wasGeneratedBy("Commit", "Commit Creation")


for title, doc in [
    ("git_commit_model_add", add),
    ("git_commit_model_mod", mod),
    ("git_commit_model_del", rem),
    ("gitlab_commit_model", com),
    ("gitlab_issue_model", iss),
    ("gitlab_merge_request_model", mr),
    ("gitlab_release_tag_model", release_tag_model)
]:
    dot = prov_to_dot(doc, show_nary=False, use_labels=False, direction="BT")
    dot.set_graph_defaults(bgcolor="transparent")
    dot.write_pdf(
        f"./pdfs/{title}.pdf"
    )
    dot = prov_to_dot(doc, show_nary=False, use_labels=False, direction="BT")
    dot.set_graph_defaults(bgcolor="transparent")
    dot.write_svg(
        f"./svgs/{title}.svg"
    )