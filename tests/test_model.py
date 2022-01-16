import pytest

from obfuskey import alphabets, ObfusKey
from obfuskey.exceptions import (
    DuplicateError,
    MultiplierError,
    NegativeValueError,
    MaximumValueError,
    UnknownValueError,
    KeyLengthError,
)


class TestObfusKey:
    def test_duplicates_in_alphabet(self) -> None:
        with pytest.raises(DuplicateError):
            ObfusKey("aabcdef")

    @pytest.mark.parametrize("multiplier", [200, 200.5])
    def test_multiplier_error(self, multiplier: int) -> None:
        with pytest.raises(MultiplierError):
            ObfusKey("abcdef", multiplier=multiplier)

    def test_key_length(self) -> None:
        key_length = 10
        obfuskey = ObfusKey("abc", key_length=key_length)

        assert obfuskey.key_length == key_length

    def test_maximum_value(self) -> None:
        maximum_value = 3 ** 6 - 1
        obfuskey = ObfusKey("abc")

        assert obfuskey.maximum_value == maximum_value

    @pytest.mark.parametrize("multiplier,expected", [(None, 1181), (123, 123)])
    def test_multiplier(self, multiplier: int, expected: int) -> None:
        obfuskey = ObfusKey("abc", multiplier=multiplier)

        assert obfuskey.multiplier == expected

    def test_set_prime_multiplier(self) -> None:
        obfuskey = ObfusKey("abc")
        obfuskey.set_prime_multiplier(1.75)

        assert obfuskey.multiplier == 1277

    @pytest.mark.parametrize(
        "alphabet,value,key",
        [
            (alphabets.BASE16, 12345, "A16A63"),
            (alphabets.BASE36, 12345, "MNYJ53"),
            (alphabets.BASE52, 12345, "ckPl95"),
            (alphabets.BASE56, 12345, "dGTZmF"),
            (alphabets.BASE58, 12345, "dWxtix"),
            (alphabets.BASE62, 12345, "d2Aasl"),
            (alphabets.BASE64, 12345, "eIq9Uz"),
            (alphabets.BASE94, 12345, "\\2'?@X"),
        ],
    )
    def test_to_key(self, alphabet: str, value: int, key: str) -> None:
        obfuskey = ObfusKey(alphabet)
        assert obfuskey.to_key(value) == key

    def test_to_key_negative(self) -> None:
        with pytest.raises(NegativeValueError):
            obfuskey = ObfusKey("abc")
            obfuskey.to_key(-1)

    def test_to_key_over_maximum_value(self) -> None:
        with pytest.raises(MaximumValueError):
            obfuskey = ObfusKey("abc")
            obfuskey.to_key(obfuskey.maximum_value + 1)

    def test_to_key_zero_value(self) -> None:
        obfuskey = ObfusKey("abc")
        assert obfuskey.to_key(0) == "aaaaaa"

    @pytest.mark.parametrize(
        "alphabet,value,key",
        [
            (alphabets.BASE16, 12345, "A16A63"),
            (alphabets.BASE36, 12345, "MNYJ53"),
            (alphabets.BASE52, 12345, "ckPl95"),
            (alphabets.BASE56, 12345, "dGTZmF"),
            (alphabets.BASE58, 12345, "dWxtix"),
            (alphabets.BASE62, 12345, "d2Aasl"),
            (alphabets.BASE64, 12345, "eIq9Uz"),
            (alphabets.BASE94, 12345, "\\2'?@X"),
        ],
    )
    def test_to_value(self, alphabet: str, value: int, key: str) -> None:
        obfuskey = ObfusKey(alphabet)
        assert obfuskey.to_value(key) == value

    def test_to_value_unknown_value(self) -> None:
        with pytest.raises(UnknownValueError):
            obfuskey = ObfusKey("abc")
            obfuskey.to_value("abcd")

    def test_to_value_over_key_length(self) -> None:
        with pytest.raises(KeyLengthError):
            obfuskey = ObfusKey("abc")
            obfuskey.to_value("a" * (obfuskey.key_length + 1))

    def test_to_value_zero_value_key(self) -> None:
        obfuskey = ObfusKey("abc")
        assert obfuskey.to_value("aaaaaa") == 0
