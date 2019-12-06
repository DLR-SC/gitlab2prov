import prov.dot
import tempfile
import os
import subprocess

from commit_model_add import COMMIT_MODEL_ADD
from commit_model_delete import COMMIT_MODEL_DELETE
from commit_model_modify import COMMIT_MODEL_MODIFY
from commit_model_event_create import COMMIT_MODEL_EVENT_CREATE
from commit_model_event_update import COMMIT_MODEL_EVENT_UPDATE


models = {
        "commit_model_add": COMMIT_MODEL_ADD, 
        "commit_model_modify": COMMIT_MODEL_MODIFY,
        "commit_model_delete": COMMIT_MODEL_DELETE,
        "commit_model_event_create": COMMIT_MODEL_EVENT_CREATE,
        "commit_model_event_update": COMMIT_MODEL_EVENT_UPDATE
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
