#!/usr/bin/env python

import argparse
import configparser
import os

from gl2p.pipes import CommitPipeline
from gl2p.utils import url_validator
from gl2p.commons import ConfigurationException, URLException

from prov.dot import prov_to_dot


def drain_pipelines(config):
    pipelines = [CommitPipeline(config)]
    for pipe in pipelines:
        pipe.request_data()
        pipe.translate_data()
        prov = pipe.commit_data()
        # create dotfile
        dot = open("prov.dot", "w")
        print(prov_to_dot(prov), file=dot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitLab repo to prov doc")
    config = configparser.ConfigParser()
    parser.add_argument("url", help="url to gilab repository")
    parser.add_argument("config", help="path to config file")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        raise ConfigurationException("Config file path invalid.")
    config.read(args.config)

    if not url_validator(args.url):
        raise URLException("URL invalid.")
    config["GITLAB"]["project"] = args.url

    # TODO: maybe another way to pass the config
    # also ... serious names
    drain_pipelines(config)
