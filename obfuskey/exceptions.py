from __future__ import annotations


class ObfuskeyError(Exception):
    """The base exception class of BaseHash"""

    pass


class BitOverflowError(ObfuskeyError):
    """Raised when a value provided for bit packing exceeds its allocated bit capacity in the schema."""

    pass


class DuplicateError(ObfuskeyError):
    """Raised when the provided alphabet contains duplicate characters"""

    pass


class KeyLengthError(ObfuskeyError):
    """Raised when there is an issue with the key length"""

    pass


class MaximumValueError(ObfuskeyError):
    """Raised when the value bring processed is too large"""

    pass


class MultiplierError(ObfuskeyError):
    """Raised when the multiplier is not an odd integer"""

    pass


class NegativeValueError(ObfuskeyError):
    """Raised when a negative value is provided"""

    pass


class SchemaValidationError(ObfuskeyError):
    """Raised when the provided schema for Obfusbit is invalid or malformed."""

    pass


class UnknownKeyError(ObfuskeyError):
    """Raised when an encoded value contains characters not found in the alphabet"""

    pass


__all__ = (
    "ObfuskeyError",
    "DuplicateError",
    "KeyLengthError",
    "MaximumValueError",
    "MultiplierError",
    "NegativeValueError",
    "UnknownKeyError",
    "BitOverflowError",
    "SchemaValidationError",
)
