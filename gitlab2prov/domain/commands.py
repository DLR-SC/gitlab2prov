from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from prov.model import ProvDocument


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
class Normalize(Command):
    document: ProvDocument
    no_duplicates: bool = False
    use_pseudonyms: bool = False
    agent_mapping: str = ""

 
@dataclass
class Combine(Command):
    documents: list[ProvDocument]


@dataclass
class Statistics(Command):
    document: ProvDocument
    resolution: str
    format: str


@dataclass
class Serialize(Command):
    url: str = None
    

@dataclass
class Document2File(Command):
    document: ProvDocument
    filename: Optional[str] = None
    format: Optional[str] = None
    

@dataclass
class File2Document(Command):
    source: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None