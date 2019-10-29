from configparser import ConfigParser
import os


class ConfigurationException(Exception):
    pass


CONFIG_PATH = "config/config.ini"
VALID_CONFIG = {
        "GITLAB":
        [
            "token",
            "url",
            "project"
        ],
        "NEO4J":
        [
            "host",
            "user",
            "password"
        ]
    }

if not os.path.exists(CONFIG_PATH):
    raise ConfigurationException(f"Missing CONFIG file: {CONFIG_PATH}")

CONFIG = ConfigParser()
CONFIG.read(CONFIG_PATH)

for section in VALID_CONFIG.keys():
    if section not in CONFIG.sections():
        raise ConfigurationException(f"Section {section} is missing!")
    for param in VALID_CONFIG[section]:
        if param not in CONFIG[section]:
            raise ConfigurationException(f"Parameter {param} in section {section} is missing!")
# TODO: also check types of content ?
