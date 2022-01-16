import pytest

from obfuskey import alphabets, utils
from obfuskey.exceptions import NegativeValueError, UnknownValueError


class TestUtil:
    def test_decode_duplicate(self) -> None:
        with pytest.raises(UnknownValueError):
            key = "test"
            utils.decode(key, alphabets.BASE36)

    def test_decode_single_digit(self) -> None:
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
        ],
    )
    def test_decode(self, alphabet: str, key: str, expected: int) -> None:
        assert utils.decode(key, alphabet) == expected

    def test_encode_negative_value(self) -> None:
        with pytest.raises(NegativeValueError):
            value = -1
            utils.encode(value, alphabets.BASE36)

    def test_encode_less_than_alphabet_length(self) -> None:
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
        ],
    )
    def test_encode(
        self,
        alphabet: str,
        value: int,
        expected: str,
    ) -> None:
        assert utils.encode(value, alphabet) == expected

    def test_prime_multiplier(self) -> None:
        prime = 4564651716269
        assert utils.generate_prime(alphabets.BASE36, 8) == prime

    def test_prime_multiplier_with_custom_multiplier(self) -> None:
        prime = 4936942338091
        assert utils.generate_prime(alphabets.BASE36, 8, prime_multiplier=1.75) == prime
