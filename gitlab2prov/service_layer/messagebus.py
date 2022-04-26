import logging
from typing import Callable

from gitlab2prov.domain import commands
from gitlab2prov.service_layer import unit_of_work


logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        handlers: dict[type[commands.Command], list[Callable]],
    ):
        self.uow = uow
        self.handlers = handlers

    def handle(self, command: commands.Command):
        for handler in self.handlers[type(command)]:
            try:
                logger.debug(f"Handling command {command}.")
                handler(command)
            except Exception:
                logger.exception(f"Exception handling command {command}.")
                raise