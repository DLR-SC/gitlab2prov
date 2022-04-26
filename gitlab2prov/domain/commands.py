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
class Update(Fetch):
    last_updated_at: datetime


@dataclass
class Serialize(Command):
    format: str
    pseudonymize: bool
    uncover_double_agents: str
