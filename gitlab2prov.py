#!/usr/bin/env python
import argparse
from gl2p.pipes import CommitPipeline
from gl2p.utils import url_validator
from gl2p.commons import URLException
from gl2p.config import CONFIG

from provdbconnector import ProvDb
from provdbconnector.db_adapters.neo4j.neo4jadapter import Neo4jAdapter
from prov.dot import prov_to_dot


def drain_pipelines():
    pipelines = [CommitPipeline()]
    for pipe in pipelines:
        pipe.request_data()
        pipe.process_data()
        pipe.translate_data()
        prov = pipe.commit_data()
    return prov


def to_neo4j(prov):
    # TODO: fix provdbconnector error
    # provdbconnector.exceptions.database.MergeException:
    # The attributes [<QualifiedName: prov:role>, 'meta:prov_type', 'meta:identifier', 'meta:namespaces', 'meta:type_map']
    # could not merged into the existing node
    auth_info = {
            "user_name": CONFIG["NEO4J"]["user"],
            "user_password": CONFIG["NEO4J"]["password"],
            "host": CONFIG["NEO4J"]["host"]
            }
    prov_api = ProvDb(adapter=Neo4jAdapter, auth_info=auth_info)
    prov_api.save_document(prov)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitLab repo to prov doc")
    parser.add_argument("url", help="url to gilab repository")
    args = parser.parse_args()

    if not url_validator(args.url):
        raise URLException("URL invalid.")
    CONFIG["GITLAB"]["project"] = args.url

    prov = drain_pipelines()
    dotfile = open("prov.dot", "w")
    print(prov_to_dot(prov), file=dotfile)
    print(prov)
    # to_neo4j(prov)
