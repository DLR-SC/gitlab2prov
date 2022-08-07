from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Command:
    pass


@dataclass
class Fetch(Command):
    url: str
    token: str


@dataclass
class Update(Fetch):
    last_updated_at: datetime


@dataclass
class Reset(Command):
    pass


@dataclass
class Serialize(Command):
    format: str
    pseudonymize: bool
    uncover_double_agents: str
    out: Optional[str] = None
