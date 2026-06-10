"""Containers — domain kit host (virgin boot ships base only)."""

from .base import DomainContainer

__all__ = ["DomainContainer"]


def __getattr__(name: str):
    if name == "ConstructionContainer":
        from .construction import ConstructionContainer

        return ConstructionContainer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
