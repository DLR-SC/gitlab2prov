import prov.dot
import tempfile
import os
import subprocess

from commit_model_add_file import COMMIT_MODEL_ADD_FILE
from commit_model_delete_file import COMMIT_MODEL_DELETE_FILE
from commit_model_modify_file import COMMIT_MODEL_MODIFY_FILE
from commit_model_new_commit import COMMIT_MODEL_NEW_COMMIT
from commit_model_new_commit_event import COMMIT_MODEL_NEW_COMMIT_EVENT

from issue_model_new_issue import ISSUE_MODEL_NEW_ISSUE
from issue_model_new_issue_event import ISSUE_MODEL_NEW_ISSUE_EVENT
from issue_model_marked_as_duplicate import ISSUE_MODEL_MARKED_AS_DUPLICATE


models = {
        "commit_model_add_file": COMMIT_MODEL_ADD_FILE, 
        "commit_model_modify_file": COMMIT_MODEL_MODIFY_FILE,
        "commit_model_delete_file": COMMIT_MODEL_DELETE_FILE,
        "commit_model_new_commit": COMMIT_MODEL_NEW_COMMIT,
        "commit_model_new_commit_event": COMMIT_MODEL_NEW_COMMIT_EVENT,
        "issue_model_new_issue": ISSUE_MODEL_NEW_ISSUE,
        "issue_model_new_issue_event": ISSUE_MODEL_NEW_ISSUE_EVENT,
        "issue_model_marked_as_duplicate": ISSUE_MODEL_MARKED_AS_DUPLICATE
        }

layouts = {}

def add_layout(dotfile, layout):
    # hacky, watch out
    if not layout: 
        return dotfile
    dotfile = str(dotfile)
    split = dotfile.split("}")
    for le in layout:
        split[-2] += le + "\n"
    return "}".join(split)


for title, doc in models.items():
    print(f"-- {title}")
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "w") as tmp:
            dot = prov.dot.prov_to_dot(doc, show_nary=False)
            print(add_layout(dot, layouts.get(title)), file=tmp)
    finally:
        subprocess.run(["dot", "-n", "-Tpng", "-Gdpi=200", path, "-o", f"pngs/{title}.png"])
        os.remove(path)
