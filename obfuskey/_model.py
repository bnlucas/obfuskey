from obfuskey._constants import KEY_LENGTH, PRIME_MULTIPLIER
from obfuskey._types import FloatType
from obfuskey.utils import decode, encode, generate_prime
from obfuskey.exceptions import (
    DuplicateError,
    KeyLengthError,
    MaximumValueError,
    MultiplierError,
    NegativeValueError,
    UnknownValueError,
)


class ObfusKey:
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

    @property
    def key_length(self) -> int:
        return self.__key_length

    @property
    def maximum_value(self) -> int:
        return self.__maximum_value

    @property
    def multiplier(self) -> int:
        if self.__multiplier is None:
            self.__generate_multiplier()

        return self.__multiplier

    def set_prime_multiplier(self, multiplier: FloatType) -> None:
        self.__prime_multiplier = multiplier

    def to_key(self, value: int) -> str:
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
        if not all(c in self.__alphabet for c in set(key)):
            raise UnknownValueError(
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

        return key * pow(self.__multiplier, -1, max_p1) % max_p1

    def __generate_multiplier(self) -> None:
        self.__multiplier = generate_prime(
            self.__alphabet,
            self.__key_length,
            prime_multiplier=self.__prime_multiplier,
        )
