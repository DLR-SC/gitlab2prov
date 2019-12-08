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


from urllib.parse import urlparse
import uuid

def pathify(url):
    return urlparse(url).path.replace("/", "", 1).replace("/", "%2F")

def namify(string):   
    replacements = {"-": ["/", ".", " ", ";", ":", "%"]}
    for rep, sublist in replacements.items():
        for sub in sublist:
            string = string.replace(sub, rep)
    return string

def url_validator(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False

def unique_id(*strings):
    # probabilistic unique hash
    # based on uuid5 (sha1)
    strings = map(str, sorted(strings))
    string = "".join(strings)
    # avoid collision with commit shas by prepending "ID-"
    return "ID-" + uuid.uuid5(uuid.NAMESPACE_DNS, string).hex

