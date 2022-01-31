import random
import pytest

from obfuskey import __version__, alphabets, Obfuskey
from obfuskey.exceptions import (
    DuplicateError,
    MultiplierError,
    NegativeValueError,
    MaximumValueError,
    UnknownKeyError,
    KeyLengthError,
)


def test_version():
    assert __version__ == "0.1.3"


class TestObfusKey:
    def test_obfuskey(self) -> None:
        key_length = random.randint(1, 32)
        obfuskey = Obfuskey(random.choice(alphabets.__all__), key_length=key_length)
        expected = random.randint(0, obfuskey.maximum_value)

        key = obfuskey.get_key(expected)
        assert key != expected

        actual = obfuskey.get_value(key)
        assert expected == actual

    def test_duplicates_in_alphabet(self) -> None:
        with pytest.raises(DuplicateError):
            Obfuskey("aabcdef")

    @pytest.mark.parametrize("multiplier", [200, 200.5])
    def test_multiplier_error(self, multiplier: int) -> None:
        with pytest.raises(MultiplierError):
            Obfuskey("abcdef", multiplier=multiplier)

    def test_key_length(self) -> None:
        key_length = 10
        obfuskey = Obfuskey("abc", key_length=key_length)

        assert obfuskey.key_length == key_length

    def test_maximum_value(self) -> None:
        maximum_value = 3**6 - 1
        obfuskey = Obfuskey("abc")

        assert obfuskey.maximum_value == maximum_value

    @pytest.mark.parametrize("multiplier,expected", [(None, 1181), (123, 123)])
    def test_multiplier(self, multiplier: int, expected: int) -> None:
        obfuskey = Obfuskey("abc", multiplier=multiplier)

        assert obfuskey.multiplier == expected

    def test_set_prime_multiplier(self) -> None:
        obfuskey = Obfuskey("abc")
        obfuskey.set_prime_multiplier(1.75)

        assert obfuskey.multiplier == 1277

    @pytest.mark.parametrize(
        "alphabet,value,key",
        [
            (alphabets.BASE16, 12345, "A16A63"),
            (alphabets.BASE32, 12345, "O6VAF5"),
            (alphabets.BASE36, 12345, "MNYJ53"),
            (alphabets.BASE52, 12345, "ckPl95"),
            (alphabets.BASE56, 12345, "dGTZmF"),
            (alphabets.BASE58, 12345, "dWxtix"),
            (alphabets.BASE62, 12345, "d2Aasl"),
            (alphabets.BASE64, 12345, "eIq9Uz"),
            (alphabets.BASE94, 12345, "\\2'?@X"),
        ],
    )
    def test_get_key(self, alphabet: str, value: int, key: str) -> None:
        obfuskey = Obfuskey(alphabet)
        assert obfuskey.get_key(value) == key

    def test_get_key_negative(self) -> None:
        with pytest.raises(NegativeValueError):
            obfuskey = Obfuskey("abc")
            obfuskey.get_key(-1)

    def test_get_key_over_maximum_value(self) -> None:
        with pytest.raises(MaximumValueError):
            obfuskey = Obfuskey("abc")
            obfuskey.get_key(obfuskey.maximum_value + 1)

    def test_get_key_zero_value(self) -> None:
        obfuskey = Obfuskey("abc")
        assert obfuskey.get_key(0) == "aaaaaa"

    @pytest.mark.parametrize(
        "alphabet,value,key",
        [
            (alphabets.BASE16, 12345, "A16A63"),
            (alphabets.BASE32, 12345, "O6VAF5"),
            (alphabets.BASE36, 12345, "MNYJ53"),
            (alphabets.BASE52, 12345, "ckPl95"),
            (alphabets.BASE56, 12345, "dGTZmF"),
            (alphabets.BASE58, 12345, "dWxtix"),
            (alphabets.BASE62, 12345, "d2Aasl"),
            (alphabets.BASE64, 12345, "eIq9Uz"),
            (alphabets.BASE94, 12345, "\\2'?@X"),
        ],
    )
    def test_get_value(self, alphabet: str, value: int, key: str) -> None:
        obfuskey = Obfuskey(alphabet)
        assert obfuskey.get_value(key) == value

    def test_get_value_unknown_value(self) -> None:
        with pytest.raises(UnknownKeyError):
            obfuskey = Obfuskey("abc")
            obfuskey.get_value("abcd")

    def test_get_value_over_key_length(self) -> None:
        with pytest.raises(KeyLengthError):
            obfuskey = Obfuskey("abc")
            obfuskey.get_value("a" * (obfuskey.key_length + 1))

    def test_get_value_zero_value_key(self) -> None:
        obfuskey = Obfuskey("abc")
        assert obfuskey.get_value("aaaaaa") == 0
