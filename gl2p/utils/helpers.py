# Copyright (c) 2019 German Aerospace Center (DLR/SC).
# All rights reserved.
#
# This file is part of gitlab2prov.
# gitlab2prov is licensed under the terms of the MIT License.
# SPDX short Identifier: MIT
#
# You may obtain a copy of the License at:
# https://opensource.org/licenses/MIT
#
# A command line tool to extract provenance data (PROV W3C)
# from GitLab hosted repositories aswell as to store the extracted data in a Neo4J database.
#
# code-author: Claas de Boer <claas.deboer@dlr.de>
"""
Helper functions.
"""


import datetime
import urllib.parse
import uuid
from typing import Any, Iterator, List
from gl2p.utils.objects import GL2PEvent


def ptime(string: str) -> datetime.datetime:
    """
    Parse datetimestring to datetime object.
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    date = datetime.datetime.strptime(string, fmt)
    return date


def by_date(event: GL2PEvent) -> datetime.datetime:
    """
    Parse value of key 'created_at' of resource to datetime object.
    """
    return ptime(event.created_at)


def chunks(lst: List[Any], chunk_size: int) -> Iterator[List[Any]]:
    """
    Generator for n-sized chunks of list l.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i: i+chunk_size]


def url_encoded_path(url: str) -> str:
    """
    Extract project path from url and replace "/" by "%2F".
    """
    path = urllib.parse.urlparse(url).path

    if path.endswith("/"):
        path = path[:-1]

    if not path:
        return ""

    return path[1:].replace("/", "%2F")


def qname(string: str) -> str:
    """
    Return uuid5 of *string* in string representation.

    Used to create unique identifiers.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, string))
