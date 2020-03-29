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
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: expected type str, got type {type(string)}.")

    fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
    return datetime.datetime.strptime(string, fmt)


def by_date(event: GL2PEvent) -> datetime.datetime:
    """
    Parse value of attribute 'created_at' of resource to datetime object.
    """
    if not isinstance(event, GL2PEvent):
        raise TypeError(f"Parameter event: Expected type GL2PEvent, got type {type(event)}.")

    return ptime(event.created_at)


def chunks(L: List[Any], chunk_size: int) -> Iterator[List[Any]]:
    """
    Generator for n-sized chunks of list *L*.
    """
    if chunk_size is None or chunk_size == 0:
        raise ValueError(f"Parameter chunk_size: Unexpected value {chunk_size}.")

    if not isinstance(L, list):
        raise TypeError(f"Parameter L: Expected type list, got type {type(L)}.")

    if not isinstance(chunk_size, int):
        raise TypeError(f"Parameter chunk_size: Expected type int, got type {type(chunk_size)}.")

    for i in range(0, len(L), chunk_size):
        yield L[i: i+chunk_size]


def url_encoded_path(url: str) -> str:
    """
    Extract project path from url and replace "/" by "%2F".
    """
    if not isinstance(url, str):
        raise TypeError(f"Parameter url: Expected type str, got type {type(url)}.")

    path = urllib.parse.urlparse(url).path
    
    if not path:
        raise ValueError(f"Could not parse path from {url}.")

    if path.endswith("/"):
        path = path[:-1]

    if not path:
        raise ValueError(f"Empty path parsed from {url}.")

    return path[1:].replace("/", "%2F")


def qname(string: str) -> str:
    """
    Return string representation of uuid5 of *string*.
    
    Creates unique identifiers.
    """
    if not isinstance(string, str):
        raise TypeError(f"Parameter string: Expected type str, got type {type(string)}.")

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, string))
