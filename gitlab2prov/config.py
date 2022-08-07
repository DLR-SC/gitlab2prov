import os
from typing import Any

import json
import jsonschema
from ruamel.yaml import YAML
from gitlab2prov.root import get_package_root


def parse_option(name: str, value: list[str] | str | bool):
    if isinstance(value, list):
        for item in value:
            yield f"--{name}"
            yield item
    elif isinstance(value, bool):
        yield f"--{name}"
    else:
        yield f"--{name}"
        yield value


def parse_array(array: list[dict[str, Any]]):
    for object in array:
        command, optlist = next(iter(object.items()))
        yield command

        if optlist is None:
            continue

        for name, value in optlist.items():
            yield from parse_option(name, value)


def read_file(filepath):
    with open(filepath, "rt") as f:
        yaml = YAML(typ="safe")
        return yaml.load(f.read())


def read_args_from_file(filepath) -> list[str]:
    ok, err = validate(filepath)
    if not ok:
        raise err
    return list(parse_array(read_file(filepath)))


def get_schema():
    schema_path = os.path.join(get_package_root(), "schema.json")
    with open(schema_path, "rt", encoding="utf-8") as fid:
        return json.loads(fid.read())


def validate(fp):
    try:
        jsonschema.validate(read_file(fp), get_schema())
    except Exception as err:
        return False, err
    return True, "valid"

