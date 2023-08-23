"""
mlte/private/meta.py

Metaclasses helpers.
"""


def has_callable(type, name) -> bool:
    """Determine if `type` has a callable attribute with the given name."""
    return hasattr(type, name) and callable(getattr(type, name))


def has_callables(type, *names: str) -> bool:
    """ "Determine if `type` has callables with the given names."""
    return all(has_callable(type, name) for name in names)