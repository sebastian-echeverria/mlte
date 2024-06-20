"""
mlte/backend/api/endpoints/user.py

User CRUD endpoint. Note that all endpoints return a BasicUser instead of a User,
which automatically removes the hashed password from the model returned.
"""
from __future__ import annotations

import traceback as tb
from typing import List, Union

from fastapi import APIRouter, HTTPException

import mlte.backend.api.codes as codes
import mlte.store.error as errors
from mlte.backend.api import dependencies
from mlte.backend.api.auth import authorization
from mlte.backend.api.auth.authorization import AuthorizedUser
from mlte.store.user.policy import Policy
from mlte.user.model import (
    BasicUser,
    MethodType,
    Permission,
    ResourceType,
    UserWithPassword,
)

# The router exported by this submodule
router = APIRouter()


@router.get("/user/me")
def read_users_me(
    current_user: AuthorizedUser,
) -> BasicUser:
    return current_user


@router.post("/user")
def create_user(
    *,
    user: UserWithPassword,
    current_user: AuthorizedUser,
) -> BasicUser:
    """
    Create a MLTE user.
    :param user: The user to create
    :return: The created user
    """
    new_user: BasicUser
    with dependencies.user_store_session() as user_store:
        try:
            new_user = user_store.user_mapper.create(user)

            # Now create permissions and groups associated to it.
            Policy.create(
                ResourceType.USER,
                new_user.username,
                user_store,
                BasicUser(**new_user.model_dump()),
            )

            return new_user
        except errors.ErrorAlreadyExists as e:
            raise HTTPException(
                status_code=codes.ALREADY_EXISTS, detail=f"{e} already exists."
            )
        except Exception as e:
            print(f"Internal server error: {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )


@router.put("/user")
def edit_user(
    *,
    user: Union[UserWithPassword, BasicUser],
    current_user: AuthorizedUser,
) -> BasicUser:
    """
    Edit a MLTE user.
    :param user: The user to edit
    :return: The edited user
    """
    with dependencies.user_store_session() as user_store:
        try:
            return user_store.user_mapper.edit(user)
        except errors.ErrorNotFound as e:
            raise HTTPException(
                status_code=codes.NOT_FOUND, detail=f"{e} not found."
            )
        except Exception as e:
            print(f"Internal server error. {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )


@router.get("/user/{username}")
def read_user(
    *,
    username: str,
    current_user: AuthorizedUser,
) -> BasicUser:
    """
    Read a MLTE user.
    :param username: The username
    :return: The read user
    """
    with dependencies.user_store_session() as user_store:
        try:
            return user_store.user_mapper.read(username)
        except errors.ErrorNotFound as e:
            raise HTTPException(
                status_code=codes.NOT_FOUND, detail=f"{e} not found."
            )
        except Exception as e:
            print(f"Internal server error. {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )


@router.get("/user")
def list_users(
    current_user: AuthorizedUser,
) -> List[str]:
    """
    List MLTE users.
    :return: A collection of usernames
    """
    with dependencies.user_store_session() as user_store:
        try:
            return user_store.user_mapper.list()
        except Exception as e:
            print(f"Internal server error. {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )


@router.get("/users/details")
def list_users_details(
    current_user: AuthorizedUser,
) -> List[BasicUser]:
    """
    List MLTE users, with details for each user.
    :return: A collection of users with their details.
    """
    with dependencies.user_store_session() as user_store:
        try:
            detailed_users = []
            usernames = user_store.user_mapper.list()
            for username in usernames:
                user_details = BasicUser(
                    **user_store.user_mapper.read(username).model_dump()
                )
                detailed_users.append(user_details)
            return detailed_users
        except Exception as e:
            print(f"Internal server error. {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )


@router.delete("/user/{username}")
def delete_user(
    *,
    username: str,
    current_user: AuthorizedUser,
) -> BasicUser:
    """
    Delete a MLTE user.
    :param username: The username
    :return: The deleted user
    """
    with dependencies.user_store_session() as user_store:
        try:
            deleted_user = user_store.user_mapper.delete(username)

            # Now delete related permissions and groups.
            Policy.remove(ResourceType.USER, username, user_store)

            return deleted_user
        except errors.ErrorNotFound as e:
            raise HTTPException(
                status_code=codes.NOT_FOUND, detail=f"{e} not found."
            )
        except Exception as e:
            print(f"Internal server error. {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )


@router.get("/user/{username}/models")
def list_user_models(
    *,
    username: str,
    current_user: AuthorizedUser,
) -> List[str]:
    """
    Gets a list of models a user is authorized to read.
    :param username: The username
    :return: The list of model ids
    """
    with dependencies.artifact_store_session() as artifact_store:
        try:
            # Get all models, and filter out only the ones the user has read permissions for.
            user_models: List[str] = []
            all_models = artifact_store.list_models()
            for model_id in all_models:
                permission = Permission(
                    resource_type=ResourceType.MODEL,
                    resource_id=model_id,
                    method=MethodType.GET,
                )
                if authorization.is_authorized(current_user, permission):
                    user_models.append(model_id)
            return user_models

        except errors.ErrorNotFound as e:
            raise HTTPException(
                status_code=codes.NOT_FOUND, detail=f"{e} not found."
            )
        except Exception as e:
            print(f"Internal server error. {e}")
            print(tb.format_exc())
            raise HTTPException(
                status_code=codes.INTERNAL_ERROR,
                detail="Internal server error.",
            )
