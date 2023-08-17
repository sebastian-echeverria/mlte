"""
test/negotiation/test_negotiation_card.py

Unit tests for negotiation card.
"""

import pytest

from mlte.context.context import Context
from mlte.context.model import ModelCreate, NamespaceCreate, VersionCreate
from mlte.negotiation.negotiation_card import NegotiationCard
from mlte.store.base import ManagedSession, Store
from mlte.store.factory import create_store

# The namespace identifier for default context
NAMESPACE_ID = "ns0"

# The mode identifier for default context
MODEL_ID = "model0"

# The version identifier for default context
VERSION_ID = "v0"


@pytest.fixture(scope="function")
def store_with_context() -> tuple[Store, Context]:
    """Create an in-memory artifact store with initial context."""
    store = create_store("memory://")
    with ManagedSession(store.session()) as handle:
        _ = handle.create_namespace(NamespaceCreate(identifier=NAMESPACE_ID))
        _ = handle.create_model(NAMESPACE_ID, ModelCreate(identifier=MODEL_ID))
        _ = handle.create_version(
            NAMESPACE_ID, MODEL_ID, VersionCreate(identifier=VERSION_ID)
        )

    return store, Context(NAMESPACE_ID, MODEL_ID, VERSION_ID)


def test_round_trip() -> None:
    """Negotiation card can be converted to model and back."""

    card = NegotiationCard("my-card")

    model = card.to_model()
    _ = NegotiationCard.from_model(model)


def test_save_load(store_with_context: tuple[Store, Context]) -> None:
    """Negotiation card can be saved to and loaded from artifact store."""
    store, ctx = store_with_context

    card = NegotiationCard("my-card")
    card.save_with(ctx, store)

    loaded = NegotiationCard.load_with("my-card", ctx, store)
    assert loaded == card
