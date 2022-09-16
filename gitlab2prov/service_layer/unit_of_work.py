from __future__ import annotations

import abc

from gitlab2prov.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    def __enter__(self) -> AbstractUnitOfWork:
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


class InMemoryUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.resources = repository.InMemoryRepository()

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
