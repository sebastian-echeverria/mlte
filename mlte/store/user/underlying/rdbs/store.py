"""
mlte/store/user/underlying/rdbs/store.py

Implementation of relational database system user store.
"""
from __future__ import annotations

from typing import List

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy_utils
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

import mlte.store.error as errors
from mlte.store.base import StoreURI
from mlte.store.user.store import UserStore, UserStoreSession
from mlte.store.user.underlying.rdbs.metadata import (
    DBBase,
    DBUser,
    init_default_user,
)
from mlte.store.user.underlying.rdbs.reader import DBReader
from mlte.user.model import User

# -----------------------------------------------------------------------------
# RelationalDBUserStore
# -----------------------------------------------------------------------------


class RelationalDBUserStore(UserStore):
    """A DB implementation of the MLTE user store."""

    def __init__(self, uri: StoreURI, **kwargs) -> None:
        super().__init__(uri=uri)

        self.engine = sqlalchemy.create_engine(uri.uri, **kwargs)
        """The underlying storage for the store."""

        # Create the DB if it doesn't exist already.
        if not sqlalchemy_utils.database_exists(self.engine.url):
            sqlalchemy_utils.create_database(self.engine.url)

        # Creates the DB items if they don't exist already.
        self._create_tables()
        self._init_tables()

    def session(self) -> RelationalDBUserStoreSession:  # type: ignore[override]
        """
        Return a session handle for the store instance.
        :return: The session handle
        """
        return RelationalDBUserStoreSession(engine=self.engine)

    def _create_tables(self):
        """Creates all items, if they don't exist already."""
        DBBase.metadata.create_all(self.engine)

    def _init_tables(self):
        """Pre-populate tables."""
        with Session(self.engine) as session:
            init_default_user(session)


# -----------------------------------------------------------------------------
# RelationalDBUserStoreSession
# -----------------------------------------------------------------------------


class RelationalDBUserStoreSession(UserStoreSession):
    """A relational DB implementation of the MLTE user store session."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        """A reference to underlying storage."""

    def close(self) -> None:
        """Close the session."""
        self.engine.dispose()

    # -------------------------------------------------------------------------
    # Structural Elements
    # -------------------------------------------------------------------------

    def create_user(self, user: User) -> User:
        with Session(self.engine) as session:
            try:
                _, _ = DBReader.get_user(user.username, session)
                raise errors.ErrorAlreadyExists(
                    f"User with identifier {user.username} already exists."
                )
            except errors.ErrorNotFound:
                # If it was not found, it means we can create it.
                user_obj = DBUser(
                    username=user.username,
                    email=user.email,
                    disabled=user.disabled,
                    hashed_password=user.hashed_password,
                )
                session.add(user_obj)
                session.commit()
                return user.model_copy()

    def read_user(self, username: str) -> User:
        with Session(self.engine) as session:
            user, _ = DBReader.get_user(username, session)
            return user

    def list_users(self) -> List[str]:
        users: List[str] = []
        with Session(self.engine) as session:
            user_objs = session.scalars(select(DBUser))
            for user_obj in user_objs:
                users.append(user_obj.username)
        return users

    def delete_user(self, username: str) -> User:
        with Session(self.engine) as session:
            user, user_obj = DBReader.get_user(username, session)
            session.delete(user_obj)
            session.commit()
            return user