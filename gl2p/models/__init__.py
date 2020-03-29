from dataclasses import InitVar, dataclass, field
from typing import Any, Deque, Set, Tuple, Union

from prov.model import ProvDocument

from gl2p.procs.meta import (Addition, CommitCreationPackage,
                             CommitModelPackage, CreationPackage, Deletion,
                             EventPackage, Modification, ResourceModelPackage)


@dataclass
class Model:
    """
    Abstract base class for a model.
    """
    project_id: InitVar[str]
    relation_store: Set[Tuple[str, str]] = field(default_factory=set)

    def __post_init__(self, project_id: str) -> None:
        """
        Create a new prov document to store the model in.

        Decode url encoded project id.
        """
        self.project_id = project_id.replace("%2F", "-")
        self.__doc = ProvDocument()
        self.__doc.set_default_namespace("gl2p:")
        self._bundle = self.__doc.bundle(self.project_id)

    def push(self, resource: Union[ResourceModelPackage, CommitModelPackage]) -> None:
        """
        Abstract method to push a resource/commit into the model.
        """
        raise NotImplementedError

    def document(self) -> ProvDocument:
        """
        Return the model document.
        """
        return self.__doc.unified()

    def unique_specialization_of(self, start: str, target: str) -> bool:
        """
        Return whether nodes *start* and *target* are already related by a specializationOf relation.

        *start* and *target* are id strings representing a node.
        """
        tp = (start, target)
        if tp not in self.relation_store:
            self.relation_store.add(tp)
            return True
        return False


@dataclass
class CommitModel(Model):
    """
    Model implementation for commit model.
    """
    def push(self, resource: Union[ResourceModelPackage, CommitModelPackage]) -> None:
        """
        Add a resource to the model.
        """
        # TODO: fix
        if isinstance(resource, ResourceModelPackage):
            raise TypeError

        _, _, commit, parents, files = resource

        self._add_commit(resource)
        for parent in parents:
            self._add_parent(resource, parent)
        for f in files:
            self._add_file(resource, f)

    def _add_commit(self, resource: CommitModelPackage) -> None:
        """
        Add commit nodes and relations of *resource* to *bundle*.
        """
        author, committer, commit, *_ = resource
        self._bundle.agent(*author)
        self._bundle.agent(*committer)
        self._bundle.activity(*commit)
        self._bundle.wasAssociatedWith(commit.id, author.id)
        self._bundle.wasAssociatedWith(commit.id, committer.id)

    def _add_parent(self, resource: CommitModelPackage, parent: Any) -> None:
        """
        Add parent nodes and relations of *parent* to *bundle*.
        """
        _, _, commit, *_ = resource
        self._bundle.activity(*parent)
        self._bundle.wasInformedBy(commit.id, parent.id)

    def _add_file(self, resource: CommitModelPackage, file_: Union[Addition, Modification, Deletion]) -> None:
        """
        Add file relations and nodes stemming from *f* to *bundle*.
        """
        author, committer, commit, *_ = resource

        if isinstance(file_, Addition):
            self._add_addition(resource, file_)

        if isinstance(file_, Modification):
            self._add_modification(resource, file_)

        if isinstance(file_, Deletion):
            self._add_deletion(resource, file_)

    def _add_addition(self, resource: CommitModelPackage, addition: Addition) -> None:
        """
        Add file change addition relations and nodes to the model.
        """
        author, committer, commit, *_ = resource

        f, fv = addition
        self._bundle.entity(*f)
        self._bundle.entity(*fv)
        self._bundle.wasGeneratedBy(f.id, commit.id)
        self._bundle.wasGeneratedBy(fv.id, commit.id)
        self._bundle.wasAttributedTo(f.id, author.id)
        self._bundle.wasAttributedTo(fv.id, author.id)
        if self.unique_specialization_of(fv.id, f.id):
            self._bundle.specializationOf(fv.id, f.id)

    def _add_modification(self, resource: CommitModelPackage, modification: Modification) -> None:
        """
        Add file change modification relations and nodes to the model.
        """
        author, committer, commit, *_ = resource

        f, fv, fv_1s = modification
        self._bundle.entity(*f)
        self._bundle.entity(*fv)
        self._bundle.wasAttributedTo(fv.id, author.id)
        self._bundle.wasGeneratedBy(fv.id, commit.id)
        if self.unique_specialization_of(fv.id, f.id):
            self._bundle.specializationOf(fv.id, f.id)
        for fv_1 in fv_1s:
            self._bundle.entity(*fv_1)
            self._bundle.used(commit.id, fv_1.id)
            self._bundle.wasDerivedFrom(fv.id, fv_1.id)
            if self.unique_specialization_of(fv_1.id, f.id):
                self._bundle.specializationOf(fv_1.id, f.id)

    def _add_deletion(self, resource: CommitModelPackage, deletion: Deletion) -> None:
        """
        Add file change deletion relations and nodes to the model.
        """
        author, committer, commit, *_ = resource

        f, fv = deletion
        self._bundle.entity(*f)
        self._bundle.entity(*fv)
        if self.unique_specialization_of(fv.id, f.id):
            self._bundle.specializationOf(fv.id, f.id)
        self._bundle.wasInvalidatedBy(fv.id, commit.id)


@dataclass
class ResourceModel(Model):
    """
    Resource Model.
    """
    def push(self, resource: Union[ResourceModelPackage, CommitModelPackage]) -> None:
        """
        Push resource into model document.
        """
        # TODO: fix
        if isinstance(resource, CommitModelPackage):
            raise TypeError

        creation, events = resource
        self._add_creation(creation)
        self._add_event_chain(events)

    def _add_creation(self, creation_bundle: Union[CreationPackage, CommitCreationPackage]) -> None:
        """
        Resource creation.
        """
        # TODO: fix
        if isinstance(creation_bundle, CommitCreationPackage):
            raise TypeError
        creator, creation, r, rv = creation_bundle

        self._bundle.activity(*creation)
        self._bundle.entity(*r)
        self._bundle.entity(*rv)
        self._bundle.agent(*creator)

        self._bundle.wasAssociatedWith(creation.id, creator.id)
        self._bundle.wasAttributedTo(r.id, creator.id)
        self._bundle.wasAttributedTo(rv.id, creator.id)
        self._bundle.wasGeneratedBy(r.id, creation.id)
        self._bundle.wasGeneratedBy(rv.id, creation.id)
        if self.unique_specialization_of(rv.id, r.id):
            self._bundle.specializationOf(rv.id, r.id)

    def _add_event_chain(self, events: Deque[EventPackage]) -> None:
        """
        Resource event chain.

        First package in chain denotes the creation activity.
        """
        eprev = rv_1 = None

        for event in events:
            user, e, r, rv = event

            self._bundle.entity(*r)
            self._bundle.entity(*rv)
            self._bundle.activity(*e)
            self._bundle.agent(*user)
            self._bundle.wasAssociatedWith(e.id, user.id)
            self._bundle.wasAttributedTo(rv.id, user.id)
            if self.unique_specialization_of(rv.id, r.id):
                self._bundle.specializationOf(rv.id, r.id)

            # add following relations for all after the first element
            if eprev and rv_1:
                self._bundle.wasGeneratedBy(rv.id, e.id)
                self._bundle.activity(*eprev)
                self._bundle.entity(*rv_1)
                self._bundle.used(e.id, rv_1.id)
                self._bundle.wasDerivedFrom(rv.id, rv_1.id)
                self._bundle.wasInformedBy(e.id, eprev.id)

            # udpate cached previous event
            # and previous resource version
            eprev, rv_1 = e, rv


@dataclass
class CommitResourceModel(ResourceModel):
    """
    Commit resource model.
    """
    def _add_creation(self, creation_bundle: Union[CreationPackage, CommitCreationPackage]) -> None:
        """
        Commit resource creation.
        """
        # TODO: fix
        if isinstance(creation_bundle, CreationPackage):
            raise TypeError

        committer, commit, creation, r, rv = creation_bundle

        self._bundle.activity(*commit)
        self._bundle.activity(*creation)
        self._bundle.agent(*committer)
        self._bundle.entity(*r)
        self._bundle.entity(*rv)

        self._bundle.wasAssociatedWith(commit.id, committer.id)
        self._bundle.wasAssociatedWith(creation.id, committer.id)
        self._bundle.wasAttributedTo(r.id, committer.id)
        self._bundle.wasInformedBy(creation.id, commit.id)
        self._bundle.wasAttributedTo(rv.id, committer.id)
        self._bundle.wasGeneratedBy(r.id, creation.id)
        self._bundle.wasGeneratedBy(rv.id, creation.id)
        if self.unique_specialization_of(rv.id, r.id):
            self._bundle.specializationOf(rv.id, r.id)
