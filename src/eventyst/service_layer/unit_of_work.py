#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING

from gcld_new._exceptions import SqlalchemyCommitException
from gcld_new.adapters.database.interface import get_default_session_factory
from gcld_new.domain.models import Candidate, SearchSpace
from gcld_new.repositories.base import TrackingRepository
from gcld_new.repositories.candidate_repository import CandidateRepository, get_candidate_repository
from gcld_new.repositories.search_space_repository import get_search_space_repository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker


class AbstractUnitOfWork(ABC):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.rollback()

    @abstractmethod
    def commit(self):
        ...

    @abstractmethod
    def is_open(self) -> bool:
        ...

    @abstractmethod
    def rollback(self):
        ...

    @abstractmethod
    def close(self):
        ...

    @abstractproperty
    def candidates(self) -> TrackingRepository[Candidate]:
        ...

    @abstractproperty
    def search_spaces(self) -> TrackingRepository[SearchSpace]:
        ...

    def collect_new_events(self):
        for candidate in self.candidates.seen:
            while candidate.events:
                yield candidate.events.pop(0)

        for search_space in self.search_spaces.seen:
            while search_space.events:
                yield search_space.events.pop(0)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    _session: "Session"
    session_factory: "sessionmaker"
    _candidates: CandidateRepository
    _search_spaces: TrackingRepository[SearchSpace]

    def __init__(self, session_factory: "sessionmaker" = get_default_session_factory()):
        self.session_factory = session_factory

    def __enter__(self):
        self._session = self.session_factory()
        self._candidates = get_candidate_repository(self._session)
        self._search_spaces = get_search_space_repository(self._session)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self.close()

    def commit(self):
        try:
            self._session.commit()
        except Exception as exc:
            raise SqlalchemyCommitException(exc) from exc

    def rollback(self):
        self._session.rollback()

    def close(self):
        self._session.close()

    def is_open(self):
        return self._session.is_active

    @property
    def candidates(self):
        return self._candidates

    @property
    def search_spaces(self):
        return self._search_spaces
