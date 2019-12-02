from urllib.parse import urlparse

def pathify(url):
    return urlparse(url).path.replace("/", "", 1).replace("/", "%2F")

def idfy(string):
    return namify(string).lower()

def namify(string):   
    replacements = {"-": ["/", ".", " ", ";", ":"]}
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
