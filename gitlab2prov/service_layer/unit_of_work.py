from __future__ import annotations

import abc
from collections import defaultdict

from gitlab2prov.adapters import repository


class UnitOfWork(abc.ABC):
    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()

    def reset(self):
        self._reset()

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _reset(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self):
        # self.resources = repository.InMemoryRepository()
        self.resources = defaultdict(repository.InMemoryRepository)

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)

    def _commit(self):
        pass

    def _reset(self):
        self.resources = repository.InMemoryRepository()

    def rollback(self):
        pass
