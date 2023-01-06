"""
Indicates the outcome of measurement evaluation.
"""

from __future__ import annotations
import abc

from typing import Dict, Any, Optional

from mlte._global import global_state, GlobalState
from mlte.store.api import read_result, write_result

# NOTE(Kyle): This must remain a relative import to
# circumvent a circular import issue, until we do a
# better job of decoupling some of these dependencies
from ..measurement_metadata import MeasurementMetadata


def _has_callable(type, name) -> bool:
    """Determine if `type` has a callable attribute with the given name."""
    return hasattr(type, name) and callable(getattr(type, name))


def _check_global_state(state: GlobalState):
    """
    Ensure that the global state contains
    information necessary to save/load results.
    """
    if not state.has_model():
        raise RuntimeError("Set model context prior to saving result.")
    if not state.has_artifact_store_uri():
        raise RuntimeError("Set artifact store URI prior to saving result.")


class Result(metaclass=abc.ABCMeta):
    """
    The Result class serves as the base class of all
    semantically-enriched measurement evaluation results.
    The Result provides a common interface for inspecting
    the results of measurement evaluation, and also
    encapsulates the functionality required to uniquely
    associate evaluation results with the originating measurement.
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        """Define the interface for all Result subclasses."""
        # All subclasses of Result must define serialize() and deserialize()
        return all(
            _has_callable(subclass, method)
            for method in ["serialize", "deserialize"]
        )

    def __init__(self, instance, measurement_metadata: MeasurementMetadata):
        """
        Initialize a Result instance.

        :param instance: The subclass instance
        :type instance: Measurement
        :param measurement_metadata: The generating measurement's metadata
        :type measurement: MeasurementMetdata
        """
        # Store the type of the generating measurement
        self.measurement_typename = measurement_metadata.typename
        # Store the identifier for the generating measurement
        self.measurement_identifier = measurement_metadata.identifier
        # Store the type of the result itself
        self.type = type(instance).__name__

    @abc.abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """TODO"""
        raise NotImplementedError("Cannot serialize abstract Result.")

    @staticmethod
    @abc.abstractmethod
    def deserialize(
        measurement_metadata: MeasurementMetadata, json: Dict[str, Any]
    ) -> Any:
        """TODO"""
        raise NotImplementedError("Cannot deserialize abstract Result.")

    def save(self, tag: Optional[str] = None):
        """
        Save result data to the configured artifact store.

        :param tag: An optional tag to identify groups of results
        :type tag: str
        """
        state = global_state()
        _check_global_state(state)

        model_identifier, model_version = state.get_model()
        artifact_store_uri = state.get_artifact_store_uri()

        # Use API to save to artifact store
        write_result(
            artifact_store_uri,
            model_identifier,
            model_version,
            self.measurement_identifier,
            {**self._serialize_header(), "payload": {**self.serialize()}},
            tag,
        )

    @classmethod
    def load(cls, identifier: str, version: Optional[int] = None) -> Result:
        """
        Load non-semantically-enriched result data from an artifact store.
        This data may then be passed to the type-specific load() method to
        fully-reconstruct the loaded result.

        :param identifier: The identifier for the result
        :type identifier: str
        :param version: The optional version identifier; when not specified,
        the latest version of the result is read
        :type version: int

        :return: The loaded result
        :rtype: Result
        """
        state = global_state()
        _check_global_state(state)

        model_identifier, model_version = state.get_model()
        artifact_store_uri = state.get_artifact_store_uri()

        # Use API to load from artifact store
        json = read_result(
            artifact_store_uri,
            model_identifier,
            model_version,
            identifier,
            version,
        )

        # TODO: Validate response

        return cls.deserialize(
            MeasurementMetadata(
                json["measurement_typename"], json["measurement_identifier"]
            ),
            json["payload"],
        )

    def _serialize_header(self) -> Dict[str, Any]:
        """Return the header for serialization."""
        return {
            "measurement_typename": self.measurement_typename,
            "measurement_identifier": self.measurement_identifier,
            "result_type": self.type,
        }

    @staticmethod
    def _deserialize_header(json: Dict[str, Any]) -> MeasurementMetadata:
        """TODO"""
        return MeasurementMetadata(
            json["measurement_typename"], json["measurement_identifier"]
        )
