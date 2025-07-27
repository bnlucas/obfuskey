from __future__ import annotations

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


class Obfuskey:
    """
    Constructs a new instance with a given alphabet, key length, and an optional multiplier
    to generate obfuscated keys for integers, or to reverse existing keys back into
    their original integer values.

    :param alphabet: The set of characters to use when generating and decoding keys.
                     Must not contain duplicate characters.
    :param key_length: The desired length of the generated keys. Defaults to `KEY_LENGTH`.
    :param multiplier: An optional odd integer to use as the multiplier for obfuscation.
                       If `None`, a prime multiplier will be generated automatically.
    :raises DuplicateError: If the provided `alphabet` contains duplicate characters.
    :raises MultiplierError: If the provided `multiplier` is not an odd integer.
    """

    def __init__(
        self,
        alphabet: str,
        *,
        key_length: int = KEY_LENGTH,
        multiplier: int = None,
    ):
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

    def __repr__(self) -> str:
        """
        Returns a string representation of the Obfuskey object.
        """
        multiplier_info = ""

        if self.__multiplier is not None:
            multiplier_info = f", multiplier={self.__multiplier}"
        else:
            multiplier_info = (
                f", multiplier=auto (prime_mult={self.__prime_multiplier})"
            )

        display_alphabet = f"'{self.__alphabet}'"
        if len(self.__alphabet) > 20:
            display_alphabet = f"'{self.__alphabet[:10]}...{self.__alphabet[-5:]}'"

        return (
            f"Obfuskey(alphabet={display_alphabet}, key_length={self.__key_length}"
            f"{multiplier_info})"
        )

    @property
    def alphabet(self) -> str:
        """
        Returns the alphabet string used by this Obfuskey instance.

        :return: The alphabet string.
        :rtype: str
        """
        return self.__alphabet

    @property
    def key_length(self) -> int:
        """
        Returns the fixed length of the keys that will be generated and expected for decoding.

        :return: The key length.
        :rtype: int
        """
        return self.__key_length

    @property
    def maximum_value(self) -> int:
        """
        Returns the maximum integer value that this Obfuskey instance is allowed to obfuscate.
        This is determined by `len(alphabet) ** key_length - 1`.

        :return: The maximum obfuscate-able value.
        :rtype: int
        """
        return self.__maximum_value

    @property
    def multiplier(self) -> int:
        """
        Returns the multiplier that is being used to obfuscate values.
        If a multiplier was not provided during initialization, it will be generated
        on the first access of this property.

        :return: The multiplier.
        :rtype: int
        """
        if self.__multiplier is None:
            self.__generate_multiplier()

        return self.__multiplier

    def set_prime_multiplier(self, multiplier: FloatType) -> None:
        """
        Sets the prime multiplier to be used when generating the next prime for the
        internal multiplier. This influences the size of the automatically generated
        multiplier.

        If this is set, any existing automatically generated multiplier will be re-generated
        on next access of the `multiplier` property.

        :param multiplier: A float or Decimal value used in the prime generation calculation.
        :rtype: None
        """
        self.__prime_multiplier = multiplier
        self.__multiplier = None

    def get_key(self, value: int) -> str:
        """
        Returns an obfuscated key (an alphanumeric string) for the given integer value.

        :param value: The integer value to generate a key from. Must be non-negative
                      and within the `maximum_value` range.
        :return: The obfuscated key as a string.
        :raises NegativeValueError: If the `value` is negative.
        :raises MaximumValueError: If the `value` is greater than the instance's `maximum_value`.
        :rtype: str
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

        value = value * self.__multiplier % (self.__maximum_value + 1)
        value = encode(value, self.__alphabet)

        return value.rjust(self.__key_length, self.__alphabet[0])

    def get_value(self, key: str) -> int:
        """
        Reverses an obfuscated key (an alphanumeric string) back to its original integer value.

        :param key: The obfuscated key string to reverse.
        :return: The original integer value.
        :raises UnknownKeyError: If the `key` contains characters not found in the instance's alphabet.
        :raises KeyLengthError: If the `key`'s length differs from the instance's `key_length`.
        :rtype: int
        """
        if not all(c in self.__alphabet for c in set(key)):
            raise UnknownKeyError(
                "The key contains characters not found in the current alphabet."
            )

        if len(key) != self.__key_length:
            raise KeyLengthError("The key length does not match the set length.")

        if key == "".rjust(self.__key_length, self.__alphabet[0]):
            return 0

        if self.__multiplier is None:
            self.__generate_multiplier()

        key = decode(key, self.__alphabet)
        max_p1 = self.__maximum_value + 1

        return key * modinv(self.__multiplier, max_p1) % max_p1

    def __generate_multiplier(self) -> None:
        """
        Generates and sets the internal multiplier. This method is called internally
        when the multiplier is needed but not yet set. It uses the `generate_prime`
        utility function to find a suitable prime number based on the instance's
        alphabet, key length, and prime multiplier.

        :rtype: None
        """
        self.__multiplier = generate_prime(
            self.__alphabet,
            self.__key_length,
            prime_multiplier=self.__prime_multiplier,
        )


__all__ = ("Obfuskey",)
