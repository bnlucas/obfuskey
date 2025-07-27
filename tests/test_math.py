from __future__ import annotations

import pytest

from obfuskey._math import (
    factor,
    is_prime,
    modinv,
    next_prime,
    small_strong_pseudoprime,
    strong_pseudoprime,
    trial_division,
)
from obfuskey.exceptions import MaximumValueError


class TestPrimalityUtils:
    """
    Pytest tests for primality utility functions in `math.py`.
    """

    @pytest.mark.parametrize(
        "n, expected_s, expected_d",
        [
            (2, 0, 1),
            (3, 1, 1),
            (5, 2, 1),
            (17, 4, 1),
            (1025, 10, 1),
            (7, 1, 3),
            (11, 1, 5),
            (29, 2, 7),
        ],
    )
    def test_factor(self, n, expected_s, expected_d):
        """
        Test the **factor** function for correct `s` and `d` values.
        """
        s, d = factor(n)

        assert s == expected_s
        assert d == expected_d
        assert (2**s) * d == n - 1
        assert d % 2 != 0

    @pytest.mark.parametrize(
        "n, expected",
        [
            (2, True),
            (3, True),
            (5, True),
            (7, True),
            (11, True),
            (13, True),
            (17, True),
            (19, True),
            (23, True),
            (29, True),
            (31, True),
            (1, False),
            (4, False),
            (6, False),
            (8, False),
            (9, False),
            (10, False),
            (15, False),
            (25, False),
            (0, False),
            (-1, False),
            (49, False),
            (97, True),
            (100, False),
            (1_999_999, False),
            (2_000_000, False),
            (2_000_003, True),
            (2_047, False),
            (3215031751, False),
            (2147483647, True),
        ],
    )
    def test_is_prime(self, n, expected):
        """
        Test the **is_prime** function for various integers.
        """
        assert is_prime(n) == expected

    @pytest.mark.parametrize(
        "n, expected",
        [
            (97, True),
            (99, False),
            (199, True),
            (201, False),
            (25, False),
            (2, True),
            (1, False),
            (0, False),
            (-5, False),
        ],
    )
    def test_trial_division(self, n, expected):
        """
        Test **trial_division** for small numbers. Note that `trial_division`
        is typically used for odd numbers greater than or equal to 3.
        """
        assert trial_division(n) == expected

    @pytest.mark.parametrize(
        "base, mod, expected_inverse",
        [
            (3, 11, 4),
            (7, 26, 15),
            (5, 7, 3),
            (17, 3120, 2753),
        ],
    )
    def test_modinv(self, base, mod, expected_inverse):
        """
        Test **modinv** for valid modular inverses.
        """
        assert modinv(base, mod) == expected_inverse

    @pytest.mark.parametrize(
        "base, mod",
        [
            (2, 4),
            (3, 6),
            (4, 10),
        ],
    )
    def test_modinv_no_inverse(self, base, mod):
        """
        Test **modinv** raises `ValueError` when the inverse does not exist
        (i.e., `base` and `mod` are not coprime).
        """
        with pytest.raises(ValueError):
            modinv(base, mod)

    @pytest.mark.parametrize(
        "n, expected_next_prime",
        [
            (0, 2),
            (1, 2),
            (2, 3),
            (3, 5),
            (4, 5),
            (5, 7),
            (6, 7),
            (7, 11),
            (10, 11),
            (100, 101),
            (1000, 1009),
            (104723, 104729),
            (1_000_000, 1_000_003),
        ],
    )
    def test_next_prime_small_numbers(self, n, expected_next_prime):
        """
        Test **next_prime** for small integers.
        """
        assert next_prime(n) == expected_next_prime

    def test_next_prime_large_number_no_gmpy2(self, monkeypatch):
        """
        Test **next_prime** raises `MaximumValueError` for large numbers
        when `gmpy2` is not installed.
        """

        class MockGmpy2:
            def __getattr__(self, name):
                raise ImportError

        monkeypatch.setitem(
            __builtins__,
            "__import__",
            lambda name, *args, **kwargs: (
                MockGmpy2() if name == "gmpy2" else __import__(name, *args, **kwargs)
            ),
        )

        with pytest.raises(MaximumValueError):
            next_prime(2**512)

    @pytest.mark.parametrize(
        "n, expected",
        [
            (2_047, False),
            (3215031751, False),
            (2_047_698_921, False),
            (1_000_003, True),
            (999_983, True),
            (1999999, False),
        ],
    )
    def test_small_strong_pseudoprime(self, n, expected):
        """
        Test **small_strong_pseudoprime** for numbers up to 2,047,698,921.
        """
        assert small_strong_pseudoprime(n) == expected

    @pytest.mark.parametrize(
        "n, base, expected",
        [
            (97, 2, True),
            (97, 3, True),
            (97, 5, True),
            (4, 2, False),
            (1, 2, False),
            (25, 2, False),
            (341, 2, False),
            (561, 2, False),
            (13, 2, True),
        ],
    )
    def test_strong_pseudoprime(self, n, base, expected):
        """
        Test **strong_pseudoprime** with various numbers and bases.
        """
        assert strong_pseudoprime(n, base) == expected
