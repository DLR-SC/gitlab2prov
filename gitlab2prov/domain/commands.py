from dataclasses import dataclass
from datetime import datetime


@dataclass
class Command:
    pass


@dataclass
class Fetch(Command):
    project_url: str
    token: str


@dataclass
    last_update: datetime
class Update(Fetch):


@dataclass
class Serialize(Command):
    fmt: bool
    pseudonymize: bool
    uncover_double_agents: Path
