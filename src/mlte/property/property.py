"""
The superclass for all model properties.
"""

from __future__ import annotations

import abc
import importlib
from typing import Type

# The names of the properties submodules
SUBMODULES = ["costs", "functionality", "fairness"]


def _has_callable(type, name) -> bool:
    """Determine if `type` has a callable attribute with the given name."""
    return hasattr(type, name) and callable(getattr(type, name))


class Property(metaclass=abc.ABCMeta):
    """The Property type represents an abstract model property."""

    @classmethod
    def __subclasshook__(cls, subclass):
        """Define the interface for all concrete properties."""
        return all(
            _has_callable(subclass, method)
            for method in ["__init__", "__repr__"]
        )

    def __init__(self, name: str, description: str, rationale: str):
        """
        Initialize a Property instance.

        :param name: The name of the property
        :type name: str
        :param description: The description of the property
        :type description: str
        :param rationale: The rationale for using the property
        :type rationale: str
        """
        self.name: str = name
        """The name of the property."""
        self.description = description
        """The description of the property."""
        self.rationale = rationale
        """The rationale for using the property."""

    def _to_json(self) -> dict[str, str]:
        """
        Save a Property instance to a JSON document.

        :return: The document
        :rtype: dict[str, str]
        """
        return {
            "name": self.name,
            "repr": repr(self),
            "description": self.description,
            "rationale": self.rationale,
        }

    @staticmethod
    def _from_json(document: dict[str, str]) -> Property:
        """
        Load a Property instance from a JSON document.

        :param document: The document for the saved property
        :type document: dict[str, str]

        :return: The loaded property
        :rtype: Property
        """
        return _load_from_document(document)


def _get_class_name(property_repr: str) -> str:
    """
    Extract the class name from the property representation.

    :param property_repr: The representation
    :type property_repr: str

    :return: The class name
    :rtype: str
    """
    return property_repr[: property_repr.index("(")]


def _load_from_document(document: dict[str, str]) -> Property:
    """
    Load a Property instance from its identifier.

    :param name: The name of the property
    :type name: str

    :return: The loaded property
    :rtype: Property
    """
    if "name" not in document or "repr" not in document:
        raise RuntimeError("Saved property is malformed.")
    property_repr = document["repr"]
    rationale = document["rationale"]

    # Extract the classname from the call
    classname = _get_class_name(property_repr)

    # Load the class type from the module
    for submodule in SUBMODULES:
        module = importlib.import_module(
            f".{submodule}", package="mlte.property"
        )
        try:
            class_: Type[Property] = getattr(module, classname)
        except AttributeError:
            continue

        # Instantiate the property
        return class_(rationale)  # type: ignore

    raise RuntimeError(f"Property {document['name']} not found")
