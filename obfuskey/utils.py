from __future__ import annotations

from decimal import Decimal

from obfuskey._constants import PRIME_MULTIPLIER
from obfuskey._math import next_prime
from obfuskey._types import FloatType
from obfuskey.exceptions import NegativeValueError, UnknownKeyError


def decode(
    value: str,
    alphabet: str,
) -> int:
    """
    Decodes a given string value into an integer using the provided alphabet.
    This function performs base conversion from a custom alphabet string representation
    to an integer.

    :param value: The string value to decode.
    :param alphabet: The alphabet string used for encoding the value. The order of characters
                     in the alphabet determines their integer value (index).
    :return: The decoded value as an integer.
    :raises UnknownKeyError: If the `value` contains characters not found in the `alphabet`.
    :rtype: int
    """
    if not all(c in alphabet for c in set(value)):
        raise UnknownKeyError(
            "The value contains characters not found in the current alphabet."
        )

    if len(value) == 1:
        return alphabet.index(value)

    base = len(alphabet)
    return sum(alphabet.index(c) * base**i for i, c in enumerate(value[::-1]))


def encode(
    value: int,
    alphabet: str,
) -> str:
    """
    Encodes a given integer value into a string using the provided alphabet.
    This function performs base conversion from an integer to a custom alphabet
    string representation.

    :param value: An integer value to encode. Must be non-negative.
    :param alphabet: The alphabet string to use for encoding. The order of characters
                     in the alphabet determines their integer value (index).
    :return: The encoded value as a string.
    :raises NegativeValueError: If the `value` is negative.
    :rtype: str
    """
    if value < 0:
        raise NegativeValueError("The value must be greater than or equal to zero.")

    if value < len(alphabet):
        return alphabet[value]

    base = len(alphabet)
    key = []

    while value > 0:
        value, i = divmod(value, base)
        key.append(alphabet[i])

    return "".join(key[::-1])


def generate_prime(
    alphabet: str,
    key_length: int,
    prime_multiplier: FloatType = PRIME_MULTIPLIER,
) -> int:
    """
    Generates a prime number suitable for use as an obfuscation multiplier.
    It calculates a target value based on the maximum possible key value
    derived from the `alphabet` and `key_length`, then multiplies it by `prime_multiplier`,
    and finally finds the next prime number greater than this target.

    :param alphabet: The alphabet string, used to determine the base for maximum value calculation.
    :param key_length: The key length, used to determine the exponent for maximum value calculation.
    :param prime_multiplier: The multiplier (float or Decimal) applied to the calculated maximum value
                             before searching for the next prime. Defaults to `PRIME_MULTIPLIER`.
    :return: The next available prime number greater than the multiplied maximum value.
    :rtype: int
    """
    if isinstance(prime_multiplier, float):
        prime_multiplier = Decimal(prime_multiplier)

    # Calculate the maximum possible value for a key of given alphabet and key_length,
    # then multiply by prime_multiplier to get the target for prime generation.
    target_value = int((len(alphabet) ** key_length - 1) * prime_multiplier)

    return next_prime(target_value)


__all__ = (
    "decode",
    "encode",
    "generate_prime",
)
