from math import gcd
from typing import Tuple

from obfuskey.exceptions import MaximumValueError

try:
    from math import isqrt
except ImportError:

    def isqrt(n: int) -> int:
        """
        integer square root.
        - In number theory, the integer square root (isqrt) of a positive integer n
          is the positive integer m which is the greatest integer less than or equal
          to the square root of n.
        """

        if n < 0:
            raise ValueError("Square root is not defined for negative numbers.")

        if n < 2:
            return 2

        a = 1 << ((1 + n.bit_length()) >> 1)

        while True:
            b = (a + n // a) >> 1

            if b >= a:
                return a

            a = b


def factor(n) -> Tuple[int, int]:
    """
    Solve for s, d where n - 1 = 2^s * d

    :param n: an integer being tested for primality
    :return: s, d
    """
    s = 0
    d = n - 1

    while d % 2 == 0:
        s += 1
        d //= 2

    return s, d


def is_prime(n: int) -> int:
    """
    Determines if an integer is prime

    :param n: the integer being tested
    :return: true if the integer is prime, else false
    """
    if n == 2:
        return True

    if gcd(n, 510510) > 1:
        return n in (2, 3, 5, 7, 11, 13, 17)

    if n < 2000000:
        return trial_division(n)

    return small_strong_pseudoprime(n)


def modinv(base: int, mod: int) -> int:
    try:
        return pow(base, -1, mod)
    except ValueError:
        g, _g = base, mod
        x, _x = 1, 0

        while _g:
            q = g // _g
            g, _g = _g, (g - q * _g)
            x, _x = _x, (x - q * _x)

        if g > 1:
            raise ValueError("There is no inverse for {} mod {}".format(base, mod))

        if x < 0:
            x = x + mod

        return x


def next_prime(n) -> int:
    """
    Determines the next prime after a given integer.

    If the integer is larger than 512-bit, the gmpy2 package is used. If this package
    is not installed, a MaximumValueError is raised.

    :param n: the starting integer
    :return: the next available prime
    """
    if n.bit_length() > 512:
        try:
            from gmpy2 import next_prime

            return next_prime(n)
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
    Checks against a composite number to identify if an integer is prime or a
    pseudoprime. This checks against bases 2, 13, 23, and 1662803.

    :param n: the integer being tested
    :return: true if the integer is thought to be prime, else false
    """
    for base in [2, 13, 23, 1662803]:
        if not strong_pseudoprime(n, base):
            return False

    return True


def strong_pseudoprime(n, base=2):
    """
    Checks against a composite number to identify if an integer in a given base is
    prime or a pseudoprime.

    :param n: the integer being tested
    :param base: the base to test against
    :return: true if the integer is thought to be prime, else false
    """
    if not n & 1:
        return False

    s, d = factor(n)
    x = pow(base, d, n)

    if x == 1:
        return True

    for i in range(s):
        if x == n - 1:
            return True

        x = pow(x, 2, n)

    return False


def trial_division(n: int) -> int:
    """
    Determines if an integer is prime by using trial division.

    :param n: the integer being tested
    :return: true if the integer is prime, else false
    """
    return all(n % i for i in range(3, isqrt(n) + 1, 2))
