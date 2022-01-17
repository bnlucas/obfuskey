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

    - If the value contains characters not found in the alphabet, an UnknownKeyError is
    raised.

    :param value: the string value to decode
    :param alphabet: the alphabet used to encode the value
    :return: the decoded value as an integer
    """
    if not all(c in alphabet for c in set(value)):
        raise UnknownKeyError(
            "The value contains characters not found in the current alphabet."
        )

    if len(value) == 1:
        return alphabet.index(value)

    base = len(alphabet)
    return sum(alphabet.index(c) * base ** i for i, c in enumerate(value[::-1]))


def encode(
    value: int,
    alphabet: str,
) -> str:
    """
    Encodes a given integer value into a string using the provided alphabet.

    - If the value is negative, a NegativeValueError is raised.

    :param value: an integer value to encode
    :param alphabet: the alphabet to use
    :return: the encoded value as a string
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
    Generates a prime number using a given alphabet, key length, and prime multiplier.
    Before finding the next available prime, the maximum possible value is multiplied
    by the prime multiplier.

    :param alphabet: the alphabet, used to determine the maximum value
    :param key_length: the key length, used to determine the maximum value
    :param prime_multiplier: Optional. The multiplier to use against the maximum value
    :return: the next available prime number
    """
    if isinstance(prime_multiplier, float):
        prime_multiplier = Decimal(prime_multiplier)

    return next_prime(int((len(alphabet) ** key_length - 1) * prime_multiplier))
