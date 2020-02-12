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


import datetime
import urllib
import uuid
from typing import Any, Dict, Iterator, List


def ptime(s: str) -> datetime.datetime:
    """
    Parse datetimestring to datetime object.
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    date = datetime.datetime.strptime(s, fmt)
    return date


def by_date(resource: Dict[str, Any]) -> datetime.datetime:
    """
    Parse value of key 'created_at' of resource to datetime object.
    """
    return ptime(resource["created_at"])


def chunks(l: List[Any], n: int) -> Iterator[List[Any]]:
    """
    Generator for n-sized chunks of list l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]


def url_encoded_path(url: str) -> str:
    """
    Extract project path from url and replace "/" by "%2F".
    """
    return urllib.parse.urlparse(url).path[1:].replace("/", "%2F")


def qname(s: str):
    """
    Return uuid5 of *string*. Used to create unique identifiers.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))
