from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from prov.model import ProvDocument


@dataclass
class Command:
    """Base class for all commands."""
    pass


@dataclass
class Fetch(Command):
    """Fetch data from cloned repository and remote projects."""
    url: str
    token: str


@dataclass
class Update(Fetch):
    """Incremental update of data from cloned repository and remote projects."""
    last_updated_at: datetime


@dataclass
class Transform(Command):
    """Apply transformations to the provenance document."""
    document: ProvDocument
    use_pseudonyms: bool = False
    remove_duplicates: bool = False
    merge_aliased_agents: str = ""

 
@dataclass
class Combine(Command):
    """Combine multiple provenance documents into one."""
    documents: list[ProvDocument]


@dataclass
class Statistics(Command):
    """Calculate statistics for the provenance document."""
    document: ProvDocument
    resolution: str
    format: str


@dataclass
class Serialize(Command):
    """Retrieve/Serialize provenance document from interal data store."""
    url: str = None
    

@dataclass
class Write(Command):
    """Write provenance document to file."""
    document: ProvDocument
    filename: Optional[str] = None
    format: Optional[str] = None
    

@dataclass
class Read(Command):
    """Read provenance document from file."""
    filename: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None