from decimal import Decimal

from obfuskey._constants import PRIME_MULTIPLIER
from obfuskey._types import FloatType
from obfuskey.exceptions import NegativeValueError, UnknownValueError

try:
    from gmpy2 import next_prime
except ImportError:
    from obfuskey._math import next_prime


def decode(
    value: str,
    alphabet: str,
) -> int:
    if not all(c in alphabet for c in set(value)):
        raise UnknownValueError(
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
    if isinstance(prime_multiplier, float):
        prime_multiplier = Decimal(prime_multiplier)

    return next_prime(int((len(alphabet) ** key_length - 1) * prime_multiplier))
