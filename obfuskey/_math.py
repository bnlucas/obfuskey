from math import gcd, isqrt

from obfuskey.exceptions import MaximumValueError


def factor(n) -> tuple[int, int]:
    """Solve for s, d where n - 1 = 2^s * d

    :param n: an integer being tested for primality
    :return:
    """
    s = 0
    d = n - 1

    while d % 2 == 0:
        s += 1
        d //= 2

    return s, d


def is_prime(n: int) -> int:
    if int(n) != n:
        raise ValueError("Non-integer value provided")

    if gcd(n, 510510) > 1:
        return n in (2, 3, 5, 7, 11, 13, 17)

    if n < 2000000:
        return trial_division(n)

    return small_strong_pseudoprime(n)


def next_prime(n) -> int:
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
    for base in [2, 13, 23, 1662803]:
        if not strong_pseudoprime(n, base):
            return False

    return True


def strong_pseudoprime(n, base=2, s=None, d=None):
    if not n & 1:
        return False

    if not s or not d:
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
    return all(n % i for i in range(3, isqrt(n) + 1, 2))
