import prov.dot
import prov.model
import argparse
import os

# Git Commit Model
# ---

# add file
document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")
bundle = document.bundle("repository")
bundle.entity("file")
bundle.entity("file_v")
bundle.agent("author")
bundle.agent("committer")
bundle.activity("commit")
bundle.activity("parent_commit")
bundle.wasAttributedTo("file", "author")
bundle.wasAttributedTo("file_v", "author")
bundle.wasGeneratedBy("file", "commit")
bundle.wasGeneratedBy("file_v", "commit")
bundle.wasAssociatedWith("commit", "author")
bundle.wasAssociatedWith("commit", "committer")
bundle.specializationOf("file_v", "file")
bundle.wasInformedBy("commit", "parent_commit")
commit_add_file = document

# modify file
document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")
bundle = document.bundle("repository")
bundle.entity("file")
bundle.entity("file_v-1")
bundle.entity("file_v")
bundle.activity("commit")
bundle.activity("parent_commit")
bundle.agent("author")
bundle.agent("committer")
bundle.wasInformedBy("commit", "parent_commit")
bundle.wasGeneratedBy("file_v", "commit")
bundle.used("commit", "file_v-1")
bundle.wasDerivedFrom("file_v", "file_v-1")
bundle.specializationOf("file_v", "file")
bundle.specializationOf("file_v-1", "file")
bundle.wasAttributedTo("file_v", "author")
bundle.wasAssociatedWith("commit", "author")
bundle.wasAssociatedWith("commit", "committer")
commit_modify_file = document

# commit delete file
document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")
bundle = document.bundle("repository")
bundle.entity("file")
bundle.entity("file_v")
bundle.activity("parent_commit")
bundle.activity("commit")
bundle.agent("author")
bundle.agent("committer")
bundle.wasInvalidatedBy("file_v", "commit")
bundle.wasInformedBy("commit", "parent_commit")
bundle.specializationOf("file_v", "file")
bundle.wasAssociatedWith("commit", "author")
bundle.wasAssociatedWith("commit", "committer")
commit_delete_file = document

# Resources (Commits, Issues, Merge Requests)
# ---

# commit resource
document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")
bundle = document.bundle("repository")
bundle.entity("resource")
bundle.entity("resource_v")
bundle.activity("commit")
bundle.activity("resource_creation")
bundle.agent("committer")
bundle.specializationOf("resource_v", "resource")
bundle.wasAttributedTo("resource", "committer")
bundle.wasAttributedTo("resource_v", "committer")
bundle.wasAssociatedWith("commit", "committer")
bundle.wasAssociatedWith("resource_creation", "committer")
bundle.wasGeneratedBy("resource", "resource_creation")
bundle.wasGeneratedBy("resource_v", "resource_creation")
bundle.wasInformedBy("resource_creation", "commit")
resource_creation_commit = document

# resource creation (Issue, Merge Request)
document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")
bundle = document.bundle("repository")
bundle.entity("resource")
bundle.entity("resource_v")
bundle.activity("resource_creation")
bundle.agent("creator")
bundle.wasGeneratedBy("resource", "resource_creation")
bundle.wasGeneratedBy("resource_v", "resource_creation")
bundle.wasAttributedTo("resource", "creator")
bundle.wasAttributedTo("resource_v", "creator")
bundle.wasAssociatedWith("resource_creation", "creator")
bundle.specializationOf("resource_v", "resource")
resource_creation = document

# resource event
document = prov.model.ProvDocument()
document.set_default_namespace("gl2p:")
bundle = document.bundle("repository")
bundle.entity("resource")
bundle.entity("resource_v-1")
bundle.entity("resource_v")
bundle.activity("event")
bundle.activity("previous_event")
bundle.agent("event_initiator")
bundle.used("event", "resource_v-1")
bundle.wasGeneratedBy("resource_v", "event")
bundle.wasDerivedFrom("resource_v", "resource_v-1")
bundle.specializationOf("resource_v", "resource")
bundle.specializationOf("resource_v-1", "resource")
bundle.wasInformedBy("event", "previous_event")
bundle.wasAssociatedWith("event", "event_initiator")
bundle.wasAttributedTo("resource_v", "event_initiator")
resource_event = document


def style(dot):

    abbreviate = {
        "wasGeneratedBy": "gen",
        "wasAttributedTo": "att",
        "wasAssociatedWith": "assoc",
        "wasInformedBy": "inf",
        "specializationOf": "spec",
        "wasInvalidatedBy": "inv",
        "alternativeOf": "alt",
        "wasDerivedFrom": "der",
    }
    for bundle in dot.get_subgraphs():
        for edge in bundle.get_edges():
            edge.set_color("black")
            edge.set_fontcolor("black")
            edge.set_labelfontcolor("black")
            label = edge.get_label()
            edge.set_label(abbreviate.get(label, label))
    return dot


def plot(title, document, directory, fmt):

    if not fmt:
        fmt = "svg"
    if not os.path.isdir(directory):
        raise Exception("Not a directory")
    if not directory.endswith("/"):
        directory = f"{directory}/"

    dot = style(prov.dot.prov_to_dot(document, show_nary=False))

    print(f"Plotting: {directory}{title}.{fmt}")
    dot.write(path=f"{directory}{title}.{fmt}", format=fmt)


argparser = argparse.ArgumentParser(description="Plot PROV models.")
argparser.add_argument("--format", type=str, help="output format.")
argparser.add_argument("directory", type=str, help="output file directory.")
args = argparser.parse_args()
directory = args.directory
fmt = args.format

supported_formats = [
        "bmp",
        "canon",
        "cmap",
        "cmapx",
        "cmapx_np",
        "dot",
        "dot_json",
        "eps",
        "fig",
        "gd",
        "gd2",
        "gif",
        "gtk",
        "gv",
        "ico",
        "imap",
        "imap_np",
        "ismap",
        "jpe",
        "jpeg",
        "jpg",
        "json",
        "json0",
        "mp",
        "pdf",
        "pic",
        "plain",
        "plain-ext",
        "png",
        "pov",
        "ps",
        "ps2",
        "svg",
        "svgz",
        "tif",
        "tiff",
        "tk",
        "vdx",
        "vml",
        "vmlz",
        "vrml",
        "wbmp",
        "webp",
        "x11",
        "xdot",
        "xdot1.2",
        "xdot1.4",
        "xdot_json",
        "xlib",
]

if fmt not in supported_formats:
    raise Exception("Unsupported Format")

try:
    plot("commit-add-file", commit_add_file, directory, fmt)
    plot("commit-modify-file", commit_modify_file, directory, fmt)
    plot("commit-delete-file", commit_delete_file, directory, fmt)
    plot("resource-creation-commit", resource_creation_commit, directory, fmt)
    plot("resource-event", resource_event, directory, fmt)
    plot("resource-creation", resource_creation, directory, fmt)
except Exception as e:
    print(e)

print("Done.")
