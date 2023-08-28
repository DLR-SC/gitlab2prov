import abc
from collections import defaultdict
from typing import Type, TypeVar, Optional, Any


R = TypeVar("R")


class Repository(abc.ABC):
    def add(self, resource: R) -> None:
        self._add(resource)

    def get(self, resource_type: Type[R], **filters: Any) -> Optional[R]:
        resource = self._get(resource_type, **filters)
        return resource

    def list_all(self, resource_type: Type[R], **filters: Any) -> list[R]:
        resources = self._list_all(resource_type, **filters)
        return resources

    @abc.abstractmethod
    def _add(self, resource: R) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, resource_type: Type[R], **filters: Any) -> Optional[R]:
        raise NotImplementedError

    @abc.abstractmethod
    def _list_all(self, resource_type: Type[R], **filters: Any) -> list[R]:
        raise NotImplementedError


class InMemoryRepository(Repository):
    # TODO: speed up retrieval
    def __init__(self):
        super().__init__()
        self.repo = defaultdict(list)

    def _add(self, resource: R) -> None:
        self.repo[type(resource)].append(resource)

    def _get(self, resource_type: Type[R], **filters: Any) -> Optional[R]:
        return next(
            (
                r
                for r in self.repo.get(resource_type, [])
                if all(getattr(r, key) == val for key, val in filters.items())
            ),
            None,
        )

    def _list_all(self, resource_type: Type[R], **filters: Any) -> list[R]:
        return [
            r
            for r in self.repo.get(resource_type, [])
            if all(getattr(r, key) == val for key, val in filters.items())
        ]
