from obfuskey._constants import KEY_LENGTH, PRIME_MULTIPLIER
from obfuskey._math import modinv
from obfuskey._types import FloatType
from obfuskey.utils import decode, encode, generate_prime
from obfuskey.exceptions import (
    DuplicateError,
    KeyLengthError,
    MaximumValueError,
    MultiplierError,
    NegativeValueError,
    UnknownKeyError,
)


class ObfusKey:
    def __init__(
        self,
        alphabet: str,
        *,
        key_length: int = KEY_LENGTH,
        multiplier: int = None,
    ):
        """
        Constructs a new instance of a given alphabet, key length, and multiplier to
        generate obfuscated keys for a given integer, or to reverse an existing key into
        it's original value.

        :param alphabet: the alphabet to use when generating keys
        :param key_length: optional. the length of the generated keys, defaults to 6
        :param multiplier: optional. the multiplier to use, defaults to a prime number
        """
        if len(set(alphabet)) != len(alphabet):
            raise DuplicateError("The alphabet contains duplicate characters.")

        if multiplier is not None and (
            not isinstance(multiplier, int) or multiplier % 2 == 0
        ):
            raise MultiplierError("The multiplier must be an odd integer.")

        self.__alphabet = alphabet
        self.__key_length = key_length
        self.__maximum_value = len(alphabet) ** key_length - 1
        self.__multiplier = multiplier
        self.__prime_multiplier = PRIME_MULTIPLIER

    @property
    def key_length(self) -> int:
        """Returns the key length that will be generated."""
        return self.__key_length

    @property
    def maximum_value(self) -> int:
        """Returns the maximum value that the instance is allowed to obfuscate."""
        return self.__maximum_value

    @property
    def multiplier(self) -> int:
        """Returns the multiplier that is being used to obfuscate values."""

        if self.__multiplier is None:
            self.__generate_multiplier()

        return self.__multiplier

    def set_prime_multiplier(self, multiplier: FloatType) -> None:
        """
        Sets the prime multiplier to be used when generating the next prime after
        base ** length - 1.

        If this is set, the existing multiplier will be removed.

        :param multiplier: either a float or Decimal value
        """

        self.__prime_multiplier = multiplier
        self.__generate_multiplier()

    def to_key(self, value: int) -> str:
        """
        Returns an obfuscated key of the given integer value.

        - If the value is negative, a NegativeValueError is raised.
        - If the value is greater than the maximum possible value, a MaximumValueError is
        raised.

        :param value: the value to generate a key from
        :return: the obfuscated key
        """

        if value < 0:
            raise NegativeValueError("The value must be greater than or equal to zero.")

        if value > self.__maximum_value:
            raise MaximumValueError(
                f"The maximum value possible is {self.__maximum_value}"
            )

        if value == 0:
            return "".rjust(self.__key_length, self.__alphabet[0])

        if self.__multiplier is None:
            self.__generate_multiplier()

        value = value * self.__multiplier % len(self.__alphabet) ** self.__key_length
        value = encode(value, self.__alphabet)

        return value.rjust(self.__key_length, self.__alphabet[0])

    def to_value(self, key: str) -> int:
        """
        Reverses an obfuscated key back to it's integer value.

        - If the key contains characters not found in the current alphabet, an
        UnknownKeyError is raised.
        - If the key's length differs from the instance's length, a KeyLengthError is
        raised.

        :param key: the key to reverse
        :return: the original integer value
        """

        if not all(c in self.__alphabet for c in set(key)):
            raise UnknownKeyError(
                "The key contains characters not found in the current alphabet."
            )

        if len(key) != self.__key_length:
            raise KeyLengthError("They key length does not match the set length.")

        if key == "".rjust(self.__key_length, self.__alphabet[0]):
            return 0

        if self.__multiplier is None:
            self.__generate_multiplier()

        key = decode(key, self.__alphabet)
        max_p1 = self.__maximum_value + 1

        return key * modinv(self.__multiplier, max_p1) % max_p1

    def __generate_multiplier(self) -> None:
        """Generates the next prime number after the instance's maximum value"""
        self.__multiplier = generate_prime(
            self.__alphabet,
            self.__key_length,
            prime_multiplier=self.__prime_multiplier,
        )
