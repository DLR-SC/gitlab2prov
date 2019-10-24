"""common structs"""

from enum import Enum

class FileAction(Enum):
    ADDED = "A"
    DELETED = "D"
    MODIFIED = "M"

class ConfigurationException(Exception):
    pass

class URLException(Exception):
    pass
