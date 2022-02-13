from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Command:
    pass


@dataclass
class Init(Command):
    url: str
    token: str
    path: Path


@dataclass
class Update(Init):
    last_update: datetime


@dataclass
class Serialize(Command):
    fmt: bool
    pseudonymize: bool
    uncover_double_agents: Path
