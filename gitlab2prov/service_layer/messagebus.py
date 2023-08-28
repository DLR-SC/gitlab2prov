import logging
from dataclasses import dataclass
from typing import Callable

from prov.model import ProvDocument

from gitlab2prov.domain.commands import Command
from gitlab2prov.service_layer.unit_of_work import UnitOfWork


logger = logging.getLogger(__name__)


@dataclass
class MessageBus:
    uow: UnitOfWork
    handlers: dict[type[Command], list[Callable]]

    def handle(self, command: Command) -> ProvDocument | None:
        for handler in self.handlers[type(command)]:
            try:
                logger.debug(f"Handling command {command}.")
                result = handler(command)
            except Exception:
                logger.exception(f"Exception handling command {command}.")
                raise
        return result
