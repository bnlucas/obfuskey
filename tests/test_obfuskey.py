from __future__ import annotations

import random
import pytest

from decimal import Decimal

from obfuskey import __version__, alphabets, Obfuskey
from obfuskey.exceptions import (
    DuplicateError,
    MultiplierError,
    NegativeValueError,
    MaximumValueError,
    UnknownKeyError,
    KeyLengthError,
)
from obfuskey._constants import PRIME_MULTIPLIER


def test_version():
    assert __version__ == "0.2.0"


class TestObfuskey:
    def test_obfuskey(self) -> None:
        key_length = random.randint(1, 32)
        obfuskey = Obfuskey(random.choice(alphabets.__all__), key_length=key_length)
        expected = random.randint(0, obfuskey.maximum_value)

        key = obfuskey.get_key(expected)
        assert key != expected

        actual = obfuskey.get_value(key)
        assert expected == actual

    @staticmethod
    def _get_expected_alphabet_repr(alphabet: str) -> str:
        if len(alphabet) > 20:
            return f"'{alphabet[:10]}...{alphabet[-5:]}'"

        return f"'{alphabet}'"

    def test_repr_default_multiplier(self):
        """
        Tests the __repr__ output when no multiplier is explicitly provided,
        and the default prime multiplier is used.
        """
        alphabet = alphabets.BASE62
        key_length = 8

        obfuskey_instance = Obfuskey(alphabet, key_length=key_length)
        expected_repr = (
            f"Obfuskey(alphabet={self._get_expected_alphabet_repr(alphabet)}, key_length={key_length}, "
            f"multiplier=auto (prime_mult={PRIME_MULTIPLIER}))"
        )

        assert repr(obfuskey_instance) == expected_repr

    def test_repr_with_specified_multiplier(self):
        """
        Tests the __repr__ output when a specific multiplier is provided.
        """
        alphabet = alphabets.BASE36
        key_length = 5
        multiplier = 123456789
        obfuskey_instance = Obfuskey(
            alphabet, key_length=key_length, multiplier=multiplier
        )

        expected_repr = (
            f"Obfuskey(alphabet={self._get_expected_alphabet_repr(alphabet)}, key_length={key_length}, "
            f"multiplier={multiplier})"
        )

        assert repr(obfuskey_instance) == expected_repr

    def test_repr_with_long_alphabet_default_multiplier(self):
        """
        Tests the __repr__ output with a very long alphabet and default multiplier,
        ensuring the alphabet is truncated in the representation.
        """
        long_alphabet_chars = [chr(i) for i in range(33, 127)]
        long_alphabet_chars.extend(["Ä", "Ö", "Ü", "ä", "ö", "ü", "ß", "é", "ñ"])
        long_alphabet = "".join(long_alphabet_chars)

        key_length = 10
        obfuskey_instance = Obfuskey(long_alphabet, key_length=key_length)

        expected_repr = (
            f"Obfuskey(alphabet={self._get_expected_alphabet_repr(long_alphabet)}, key_length={key_length}, "
            f"multiplier=auto (prime_mult={PRIME_MULTIPLIER}))"
        )

        assert repr(obfuskey_instance) == expected_repr

    def test_repr_with_long_alphabet_specified_multiplier(self):
        """
        Tests the __repr__ output with a very long alphabet and a specified multiplier,
        ensuring the alphabet is truncated in the representation.
        """
        long_alphabet_chars = [chr(i) for i in range(33, 127)]
        long_alphabet_chars.extend(["€", "£", "¥", "®", "©", "™"])
        long_alphabet = "".join(long_alphabet_chars)

        key_length = 7
        multiplier = 987654321
        obfuskey_instance = Obfuskey(
            long_alphabet, key_length=key_length, multiplier=multiplier
        )

        expected_repr = (
            f"Obfuskey(alphabet={self._get_expected_alphabet_repr(long_alphabet)}, key_length={key_length}, "
            f"multiplier={multiplier})"
        )

        assert repr(obfuskey_instance) == expected_repr

    def test_repr_after_multiplier_generation(self):
        """
        Tests the __repr__ output after the multiplier has been implicitly generated.
        """
        alphabet = alphabets.BASE62
        key_length = 3
        obfuskey_instance = Obfuskey(alphabet, key_length=key_length)

        _ = obfuskey_instance.multiplier

        expected_repr = (
            f"Obfuskey(alphabet={self._get_expected_alphabet_repr(alphabet)}, key_length={key_length}, "
            f"multiplier={obfuskey_instance.multiplier})"
        )

        assert repr(obfuskey_instance) == expected_repr

    def test_repr_after_set_prime_multiplier(self):
        """
        Tests the __repr__ output after set_prime_multiplier has been called,
        resetting the multiplier to auto-generate.
        """
        alphabet = alphabets.BASE36
        key_length = 4
        obfuskey_instance = Obfuskey(
            alphabet,
            key_length=key_length,
            multiplier=101,
        )

        new_prime_multiplier = Decimal("2.0")
        obfuskey_instance.set_prime_multiplier(new_prime_multiplier)

        expected_repr = (
            f"Obfuskey(alphabet={self._get_expected_alphabet_repr(alphabet)}, key_length={key_length}, "
            f"multiplier=auto (prime_mult={new_prime_multiplier}))"
        )

        assert repr(obfuskey_instance) == expected_repr

    def test_duplicates_in_alphabet(self) -> None:
        with pytest.raises(DuplicateError):
            Obfuskey("aabcdef")

    @pytest.mark.parametrize("multiplier", [200, 200.5])
    def test_multiplier_error(self, multiplier: int) -> None:
        with pytest.raises(MultiplierError):
            Obfuskey("abcdef", multiplier=multiplier)

    def test_alphabet(self) -> None:
        alphabet = random.choice(alphabets.__all__)
        obfuskey = Obfuskey(alphabet)

        assert obfuskey.alphabet == alphabet

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

    @pytest.mark.parametrize(
        "alphabet,value",
        [
            (alphabets.BASE16, 12345),
            (alphabets.BASE32, 12345),
            (alphabets.BASE36, 12345),
            (alphabets.BASE52, 12345),
            (alphabets.BASE56, 12345),
            (alphabets.BASE58, 12345),
            (alphabets.BASE62, 12345),
            (alphabets.BASE64, 12345),
            (alphabets.BASE94, 12345),
            (alphabets.BASE62, 0),
            (alphabets.BASE62, 1),
            (alphabets.BASE62, 1000000),
            (alphabets.BASE36, 0),
            (alphabets.BASE36, 1),
            (alphabets.BASE36, 50000),
            (alphabets.BASE94, 0),
            (alphabets.BASE94, 1),
            (alphabets.BASE94, 200000),
        ],
    )
    def test_get_key_and_get_value_roundtrip(self, alphabet: str, value: int) -> None:
        """
        Tests that a value can be correctly obfuscated and then de-obfuscated back
        to its original value for various alphabets and values.
        """

        fixed_key_length = 6
        obfuskey = Obfuskey(alphabet, key_length=fixed_key_length)

        if value > obfuskey.maximum_value:

            pytest.skip(
                f"Value {value} is too large for Obfuskey with alphabet '{alphabet}' and "
                f"key_length {fixed_key_length}. Max is {obfuskey.maximum_value}"
            )

        obfuscated_key = obfuskey.get_key(value)
        actual_value = obfuskey.get_value(obfuscated_key)

        assert actual_value == value
        assert len(obfuscated_key) == fixed_key_length
