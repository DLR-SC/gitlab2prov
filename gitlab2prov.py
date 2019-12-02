#!/usr/bin/env python

# stdlib imports
from urllib.parse import urlparse
import argparse
import subprocess
# third party imports
from provdbconnector import ProvDb
from provdbconnector import Neo4jAdapter
from prov.dot import prov_to_dot
# local imports
from gl2p.helpers import url_validator
from gl2p.commons import URLException
from gl2p.config import CONFIG
from gl2p.origin import GitLabOrigin
from gl2p.translator import Translator


class Workflow:

    def __init__(self):
        self.data = None

        self.source = None
        self.translator = Translator()
        self.connection_handler = None

    def drain(self):
        self.source.fetch()
        self.data = self.source.process()

    def translate(self):
        return self.translator.run(self.data)

    def commit(self):
        raise NotImplementedError()


def main():
    # -- flow definition --
    workflow = Workflow()

    # -- choose correct source --
    parsed = urlparse(args.url)
    if "gitlab" in parsed.netloc:
        workflow.source = GitLabOrigin()
    else:
        return

    # -- work the source --
    workflow.drain()
    print("--» SOURCE DRAINED!")

    # -- translate raw data --
    document = workflow.translate()
    print("-- Created document.")

    # -- print to file --
    provdoc = open("provdoc", "w")
    print("-- Printing doc.")
    print(document.get_provn(), file=provdoc)
    
    # -- create dot file --
    # dotfile = open("prov.dot", "w")
    # print(prov_to_dot(document), file=dotfile)

    # -- compute layout as pdf --
    # subprocess.run(["dot","-Tpdf", "prov.dot", "-o", "prov.pdf"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitLab repo to prov doc")
    parser.add_argument("url", help="url to gilab repository")
    args = parser.parse_args()

    if not url_validator(args.url):
        raise URLException("URL invalid.")
    CONFIG["GITLAB"]["project"] = args.url
    main()
