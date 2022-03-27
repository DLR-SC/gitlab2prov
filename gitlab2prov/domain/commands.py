from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Command:
    pass


@dataclass
    url: str
class Fetch(Command):
    token: str
    path: Path


@dataclass
    last_update: datetime
class Update(Fetch):


@dataclass
class Serialize(Command):
    fmt: bool
    pseudonymize: bool
    uncover_double_agents: Path
