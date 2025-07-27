from __future__ import annotations

import pytest

from decimal import Decimal
from typing import Union

from obfuskey import alphabets, utils
from obfuskey.exceptions import NegativeValueError, UnknownKeyError


class TestUtil:
    def test_decode_unknown_characters_in_key(self) -> None:
        """
        Tests that decoding a key with characters not in the alphabet raises UnknownKeyError.
        """
        with pytest.raises(UnknownKeyError):
            key = "test"
            utils.decode(key, alphabets.BASE36)

    def test_decode_single_digit(self) -> None:
        """
        Tests decoding single-character values across the entire alphabet.
        """
        alphabet = alphabets.BASE94

        for i in alphabet:
            assert utils.decode(i, alphabet) == alphabet.index(i)

    @pytest.mark.parametrize(
        "alphabet,key,expected",
        [
            (alphabets.BASE62, "2bI", 10000),
            (alphabets.BASE62, "5Ca", 20000),
            (alphabets.BASE62, "7ns", 30000),
            (alphabets.BASE62, "APA", 40000),
            (alphabets.BASE62, "D0S", 50000),
            (alphabets.BASE62, "Fbk", 60000),
            (alphabets.BASE62, "ID2", 70000),
            (alphabets.BASE62, "KoK", 80000),
            (alphabets.BASE62, "NPc", 90000),
            (alphabets.BASE62, "0", 0),
            (alphabets.BASE62, "1", 1),
            (alphabets.BASE62, "Z", alphabets.BASE62.index("Z")),
            (alphabets.BASE62, "zzzzzz", (62**6) - 1),
            (alphabets.BASE62, "10", 62),
            (alphabets.BASE62, "11", 63),
            (alphabets.BASE16, "A", 10),
            (alphabets.BASE16, "F", 15),
            (alphabets.BASE16, "10", 16),
            (alphabets.BASE16, "FFF", 4095),
            (alphabets.BASE36, "A", 10),
            (alphabets.BASE36, "Z", 35),
            (alphabets.BASE36, "10", 36),
            (alphabets.BASE36, "ZZZ", (36**3) - 1),
            (alphabets.BASE94, "!", alphabets.BASE94.index("!")),
            (alphabets.BASE94, "~", alphabets.BASE94.index("~")),
            (alphabets.BASE94, "!!", 0),
            (
                alphabets.BASE94,
                "~!",
                alphabets.BASE94.index("~") * len(alphabets.BASE94)
                + alphabets.BASE94.index("!"),
            ),
        ],
    )
    def test_decode(self, alphabet: str, key: str, expected: int) -> None:
        """
        Tests decoding various keys with different alphabets to their expected integer values.
        """
        assert utils.decode(key, alphabet) == expected

    def test_encode_negative_value(self) -> None:
        """
        Tests that encoding a negative value raises NegativeValueError.
        """
        with pytest.raises(NegativeValueError):
            value = -1
            utils.encode(value, alphabets.BASE36)

    def test_encode_less_than_alphabet_length(self) -> None:
        """
        Tests encoding values that result in single-character keys.
        """
        alphabet = alphabets.BASE94

        for i in range(len(alphabet)):
            assert utils.encode(i, alphabet) == alphabet[i]

    @pytest.mark.parametrize(
        "alphabet,value,expected",
        [
            (alphabets.BASE62, 10000, "2bI"),
            (alphabets.BASE62, 20000, "5Ca"),
            (alphabets.BASE62, 30000, "7ns"),
            (alphabets.BASE62, 40000, "APA"),
            (alphabets.BASE62, 50000, "D0S"),
            (alphabets.BASE62, 60000, "Fbk"),
            (alphabets.BASE62, 70000, "ID2"),
            (alphabets.BASE62, 80000, "KoK"),
            (alphabets.BASE62, 90000, "NPc"),
            (alphabets.BASE62, 0, "0"),
            (alphabets.BASE62, 1, "1"),
            (alphabets.BASE62, 61, "z"),
            (alphabets.BASE62, 62, "10"),
            (alphabets.BASE62, 63, "11"),
            (alphabets.BASE62, (62**6) - 1, "zzzzzz"),
            (alphabets.BASE16, 10, "A"),
            (alphabets.BASE16, 15, "F"),
            (alphabets.BASE16, 16, "10"),
            (alphabets.BASE16, 4095, "FFF"),
            (alphabets.BASE36, 10, "A"),
            (alphabets.BASE36, 35, "Z"),
            (alphabets.BASE36, 36, "10"),
            (alphabets.BASE36, (36**3) - 1, "ZZZ"),
            (alphabets.BASE94, alphabets.BASE94.index("!"), "!"),
            (alphabets.BASE94, alphabets.BASE94.index("~"), "~"),
            (
                alphabets.BASE94,
                len(alphabets.BASE94),
                alphabets.BASE94[1] + alphabets.BASE94[0],
            ),
            (
                alphabets.BASE94,
                alphabets.BASE94.index("~") * len(alphabets.BASE94)
                + alphabets.BASE94.index("!"),
                "~!",
            ),
        ],
    )
    def test_encode(
        self,
        alphabet: str,
        value: int,
        expected: str,
    ) -> None:
        """
        Tests encoding various integer values with different alphabets to their expected string keys.
        """
        assert utils.encode(value, alphabet) == expected

    @pytest.mark.parametrize(
        "alphabet,value",
        [
            (alphabets.BASE62, 0),
            (alphabets.BASE62, 1),
            (alphabets.BASE62, 61),
            (alphabets.BASE62, 62),
            (alphabets.BASE62, 12345),
            (alphabets.BASE62, 56800235583),
            (alphabets.BASE16, 0),
            (alphabets.BASE16, 15),
            (alphabets.BASE16, 16),
            (alphabets.BASE16, 1000000),
            (alphabets.BASE36, 0),
            (alphabets.BASE36, 35),
            (alphabets.BASE36, 36),
            (alphabets.BASE36, 10000000),
            (alphabets.BASE94, 0),
            (alphabets.BASE94, alphabets.BASE94.index("~")),
            (alphabets.BASE94, len(alphabets.BASE94)),
            (alphabets.BASE94, 100000000),
        ],
    )
    def test_encode_decode_roundtrip(self, alphabet: str, value: int) -> None:
        """
        Tests that an integer encoded with an alphabet can be decoded back to the original integer.
        Ensures the encode-decode cycle is lossless.
        """
        encoded_key = utils.encode(value, alphabet)
        decoded_value = utils.decode(encoded_key, alphabet)
        assert decoded_value == value

        if value > 0:
            assert encoded_key != ""

    @pytest.mark.parametrize(
        "alphabet,key_length,prime_multiplier,expected_prime",
        [
            (alphabets.BASE36, 8, utils.PRIME_MULTIPLIER, 4564651716269),
            (alphabets.BASE36, 8, 1.75, 4936942338091),
            (alphabets.BASE16, 4, utils.PRIME_MULTIPLIER, 106087),
            (alphabets.BASE16, 4, Decimal("1.0"), 65537),
            (alphabets.BASE62, 2, utils.PRIME_MULTIPLIER, 6221),
            (alphabets.BASE62, 1, utils.PRIME_MULTIPLIER, 101),
        ],
    )
    def test_generate_prime(
        self,
        alphabet: str,
        key_length: int,
        prime_multiplier: Union[float, Decimal],
        expected_prime: int,
    ) -> None:
        """
        Tests the generate_prime function with various inputs for robustness,
        ensuring it produces the expected prime numbers.
        """
        assert (
            utils.generate_prime(
                alphabet, key_length, prime_multiplier=prime_multiplier
            )
            == expected_prime
        )
