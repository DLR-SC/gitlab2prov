import json
from typing import Any
from dataclasses import dataclass, field

import jsonschema
import jsonschema.exceptions
from ruamel.yaml import YAML
import ruamel.yaml.constructor as constructor

from gitlab2prov.root import get_package_root


@dataclass
class Config:
    """A config file."""

    content: str = ""
    schema: dict[str, Any] = field(init=False)

    def __post_init__(self):
        self.schema = self.get_schema()

    @classmethod
    def read(cls, filepath: str):
        """Read the config file from the given path."""
        with open(filepath, "rt") as f:
            yaml = YAML(typ="safe")
            return cls(content=yaml.load(f.read()))

    @staticmethod
    def get_schema() -> dict[str, Any]:
        """Get the schema from the config package."""
        path = get_package_root() / "config" / "schema.json"
        with open(path, "rt", encoding="utf-8") as f:
            return json.loads(f.read())

    def validate(self) -> tuple[bool, str]:
        """Validate the config file against the schema."""
        try:
            jsonschema.validate(self.content, self.schema)
        except jsonschema.exceptions.ValidationError as err:
            return False, err.message
        except jsonschema.exceptions.SchemaError as err:
            return False, err.message
        except constructor.DuplicateKeyError as err:
            return False, err.problem
        return True, "Everything is fine!"

    def parse(self) -> list[str]:
        """Parse the config file into a list of strings."""
        args = []

        for obj in self.content:
            command = list(obj.keys())[0]
            args.append(command)

            options = obj.get(command)
            if not options:
                continue

            for name, literal in options.items():
                if isinstance(literal, bool):
                    args.append(f"--{name}")
                elif isinstance(literal, str):
                    args.append(f"--{name}")
                    args.append(literal)
                elif isinstance(literal, list):
                    for lit in literal:
                        args.append(f"--{name}")
                        args.append(lit)
                else:
                    raise ValueError(f"Unknown literal type: {type(literal)}")
        return args
