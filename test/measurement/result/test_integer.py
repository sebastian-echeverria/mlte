"""
Unit tests for Integer.
"""

import pytest

from mlte.measurement import Measurement, MeasurementMetadata
from mlte.measurement.result import Integer


class DummyMeasurementInteger(Measurement):
    def __init__(self, identifier: str):
        super().__init__(self, identifier)

    def __call__(self) -> Integer:
        return Integer(self.metadata, 1)


def test_integer_success():
    # Ensure instantiation succeeds for valid type
    m = MeasurementMetadata("typename", "identifier")
    i = Integer(m, 1)
    assert i.value == 1


def test_integer_fail():
    # Ensure instantiation fails for invalid type
    m = MeasurementMetadata("typename", "identifier")
    with pytest.raises(AssertionError):
        _ = Integer(m, 3.14)  # type: ignore


def test_integer_serde():
    # Ensure serialization and deserialization are inverses
    m = MeasurementMetadata("typename", "identifier")
    i = Integer(m, 1)

    serialized = i.serialize()
    recovered = Integer.deserialize(m, serialized)
    assert recovered == i


def test_integer_e2e():
    m = DummyMeasurementInteger("identifier")
    i = m.evaluate()
    assert isinstance(i, Integer)
    assert i.value == 1
