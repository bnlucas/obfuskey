from __future__ import annotations

from math import gcd, isqrt
from typing import Tuple

from obfuskey.exceptions import MaximumValueError


def factor(n: int) -> Tuple[int, int]:
    """
    Computes `s` and `d` such that `n - 1 = 2^s * d`, where `d` is odd.
    This is a preliminary step for Miller-Rabin primality tests.

    :param n: The integer to factor (specifically, `n-1`).
    :return: A tuple `(s, d)` representing the factored components.
    :rtype: Tuple[int, int]
    """
    s = 0
    d = n - 1

    while d % 2 == 0:
        s += 1
        d //= 2

    return s, d


def is_prime(n: int) -> bool:
    """
    Determines if an integer is a prime number.
    It uses a combination of trial division for small numbers and
    the Miller-Rabin primality test for larger numbers.

    :param n: The integer to be tested for primality.
    :return: `True` if the integer is prime, `False` otherwise.
    :rtype: bool
    """
    if n == 2:
        return True

    if n < 2 or n % 2 == 0:
        return False

    if gcd(n, 510510) > 1:
        return n in (3, 5, 7, 11, 13, 17)

    if n < 2000000:
        return trial_division(n)

    return small_strong_pseudoprime(n)


def modinv(base: int, mod: int) -> int:
    """
    Returns the modular multiplicative inverse of `base` modulo `mod`.
    This function computes `x` such that `(base * x) % mod == 1`.

    :param base: The base integer.
    :param mod: The modulus.
    :return: The modular inverse.
    :raises ValueError: If the modular inverse does not exist (i.e., `base` and `mod` are not coprime).
    :rtype: int
    """
    return pow(base, -1, mod)


def next_prime(n: int) -> int:
    """
    Determines the smallest prime number strictly greater than `n`.

    For integers larger than 512-bit, the `gmpy2` package is used for efficient
    prime generation. If `gmpy2` is not installed, a `MaximumValueError` is raised.
    For smaller integers, an optimized trial division approach is used.

    :param n: The starting integer.
    :return: The next available prime number greater than `n`.
    :raises MaximumValueError: If `n` is larger than 512-bit and `gmpy2` is not installed.
    :rtype: int
    """
    if n.bit_length() > 512:
        try:
            from gmpy2 import next_prime as gmpy2_next_prime

            return gmpy2_next_prime(n)
        except ImportError:
            raise MaximumValueError(
                "For integers larger than 512-bit, you must have gmpy2 installed."
            )

    if n < 2:
        return 2

    if n < 5:
        return [3, 5, 5][n - 2]

    gap = [
        1,
        6,
        5,
        4,
        3,
        2,
        1,
        4,
        3,
        2,
        1,
        2,
        1,
        4,
        3,
        2,
        1,
        2,
        1,
        4,
        3,
        2,
        1,
        6,
        5,
        4,
        3,
        2,
        1,
        2,
    ]

    n += 1 + (n & 1)

    if n % 3 == 0 or n % 5 == 0:
        n += gap[n % 30]

    while not is_prime(n):
        n += gap[n % 30]

    return n


def small_strong_pseudoprime(n: int) -> bool:
    """
    Performs a deterministic Miller-Rabin primality test for numbers up to 2,047,698,921.
    This function checks against a specific set of bases (2, 13, 23, and 1662803)
    which are sufficient to determine primality for numbers within this range.

    :param n: The integer being tested.
    :return: `True` if the integer is prime, `False` if it's composite.
    :rtype: bool
    """
    for base in [2, 13, 23, 1662803]:
        if not strong_pseudoprime(n, base):
            return False

    return True


def strong_pseudoprime(n: int, base: int = 2) -> bool:
    """
    Performs a single iteration of the Miller-Rabin primality test.
    It checks if `n` is a strong pseudoprime to the given `base`.

    :param n: The integer being tested for primality. Must be an odd integer greater than 2.
    :param base: The base to test against. Defaults to 2.
    :return: `True` if `n` passes the test (is likely prime or a strong pseudoprime),
             `False` if `n` is definitely composite.
    :rtype: bool
    """
    if not n & 1:
        return False

    if n == 1:
        return False

    s, d = factor(n)
    x = pow(base, d, n)

    if x == 1 or x == n - 1:
        return True

    for _ in range(s - 1):
        x = pow(x, 2, n)

        if x == n - 1:
            return True

        if x == 1:
            return False

    return False


def trial_division(n: int) -> bool:
    """
    Determines if an integer is prime by using trial division up to its square root.
    This method is efficient for relatively small numbers.

    :param n: The integer being tested for primality.
    :return: `True` if the integer is prime, `False` otherwise.
    :rtype: bool
    """
    if n <= 1:
        return False

    if n == 2:
        return True

    return all(n % i for i in range(3, isqrt(n) + 1, 2))


__all__ = (
    "factor",
    "is_prime",
    "modinv",
    "next_prime",
    "small_strong_pseudoprime",
    "strong_pseudoprime",
    "trial_division",
)
