"""
mlte/validation/condition.py

The interface for measurement validation.
"""

from __future__ import annotations

import base64
import typing
from typing import Any, Callable, List

import dill

from mlte.spec.model import ConditionModel
from mlte.validation.result import Result
from mlte.value.artifact import Value


class Condition:
    """
    The Condition class defines the interface for measurement validators.
    """

    @typing.no_type_check
    def __init__(
        self,
        name: str,
        arguments: List[Any],
        callback: Callable[[Value], Result],
    ):
        """
        Initialize a Condition instance.

        :param name: The name of the name method, for documenting purposes.
        :param callback: The callable that implements validation
        """

        self.name: str = name
        """The human-readable identifier for the name method."""

        self.arguments: List[Any] = arguments
        """The arguments used when validating the condition."""

        self.callback: Callable[[Value], Result] = callback
        """The callback that implements validation."""

    def __call__(self, value: Value) -> Result:
        """
        Invoke the validation callback

        :param value: The value of measurement evaluation

        :return: The result of measurement validation
        """
        return self.callback(value)._with_evidence_metadata(value.metadata)

    def to_model(self) -> ConditionModel:
        """
        Returns this condition as a model.

        :return: The serialized model object.
        """
        return ConditionModel(
            name=self.name,
            arguments=self.arguments,
            callback=Condition.encode_callback(self.callback),
        )

    @staticmethod
    def encode_callback(callback: Callable[[Value], Result]) -> str:
        """Encodes the callback as a base64 string."""
        return base64.b64encode(dill.dumps(callback)).decode("utf-8")

    @classmethod
    def from_model(cls, model: ConditionModel) -> Condition:
        """
        Deserialize a Condition from a model.

        :param model: The model.

        :return: The deserialized Condition
        """
        condition: Condition = Condition(
            model.name,
            model.arguments,
            dill.loads(base64.b64decode(str(model.callback).encode("utf-8"))),
        )
        return condition

    def __str__(self) -> str:
        """Return a string representation of Condition."""
        return f"{self.name}"

    # -------------------------------------------------------------------------
    # Equality Testing
    # -------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Compare Condition instances for equality."""
        # TODO: is just names enough? Should we compare args and callback?
        if not isinstance(other, Condition):
            return False
        reference: Condition = other
        return (
            self.name == reference.name
            and Condition.encode_callback(self.callback)
            == Condition.encode_callback(other.callback)
            and self.arguments == other.arguments
        )

    def __neq__(self, other: Condition) -> bool:
        """Compare Condition instances for inequality."""
        return not self.__eq__(other)
