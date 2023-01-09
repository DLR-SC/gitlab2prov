import json
from typing import Any

import jsonschema
import jsonschema.exceptions

from ruamel.yaml import YAML, constructor

from gitlab2prov.root import get_package_root


def read_file(filepath: str) -> Any:
    with open(filepath, "rt") as f:
        yaml = YAML(typ="safe")
        return yaml.load(f.read())


def get_schema() -> dict[str, Any]:
    path = get_package_root() / "config" / "schema.json"
    with open(path, "rt", encoding="utf-8") as f:
        return json.loads(f.read())


class ConfigParser:
    @staticmethod
    def validate(filepath: str) -> tuple[bool, str]:
        try:
            validator = jsonschema.Draft7Validator(get_schema())
            validator.validate(read_file(filepath))
        except jsonschema.exceptions.ValidationError as err:
            return False, err.message
        except jsonschema.exceptions.SchemaError as err:
            return False, err.message
        except constructor.DuplicateKeyError as err:
            return False, err.problem
        return True, "Everything is fine!"

    def parse(self, filepath: str) -> list[str]:
        content = read_file(filepath)
        return list(self.parse_array(content))

    def parse_array(self, arr: list[Any]):
        for obj in arr:
            yield from self.parse_object(obj)

    def parse_object(self, obj: dict[str, Any]):
        cmd = list(obj.keys())[0]
        yield cmd
        yield from self.parse_options(obj[cmd])

    def parse_options(self, options: dict[str, bool | str | list[str]] | None):
        if not options:
            return
        for name, value in options.items():
            yield from self.parse_option(name, value)

    def parse_option(self, name: str, literal: bool | str | list[str]):
        match literal:
            case bool():
                yield f"--{name}"
            case str():
                yield f"--{name}"
                yield literal
            case list() as litlist:
                for lit in litlist:
                    yield f"--{name}"
                    yield lit
            case _:
                raise ValueError(f"Unknown literal type!")
