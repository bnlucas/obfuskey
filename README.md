# ObfusKey
***

[![pypi][pypi-v]][pypi] [![license][pypi-l]][pypi] [![coverage][codecov-i]][codecov] [![build][workflow-i]][workflow]

ObfusKey is a utility for generating obfuscated keys of integer values. While working
to modernize its predecessor, [BaseHash](basehash), it was found that a lot of
simplifications could be made, thus ObfusKey was born.

ObfusKey was built solely for Python 3.6 or higher. For lower versions, you can still
use [BaseHash][basehash].

ObfusKey will generate obfuscated, reversible keys using a given alphabet and key
length. The maximum value it can process is `base ** key_length - 1`, where `base` is
the length of the provided alphabet. An optional modifier can also be provided, which is
then required when reversing the key into it's original value. If a modifier is not
provided, ObfusKey will generate the next prime integer after
`base ** key_length - 1` along with a prime modifier. The default prime modifier will
generate golden ratio primes, but this can be overwritten.

## Install

```text
$ pip install obfuskey
```

If you're building from source

```text
$ pip install .

OR

$ poetry install
```

## Usage

To use ObfusKey, you can use one of the available alphabets, or provide your own. You
can also provide your own multiplier, or leave it blank to use the built-in prime
generator.

```python
from obfuskey import ObfusKey, alphabets


obfuscator = ObfusKey(alphabets.BASE36, key_length=8)

key = obfuscator.to_key(1234567890)     # FWQ8H52I
value = obfuscator.to_value('FWQ8H52I') # 1234567890
```

To provide a custom multiplier, or if you to provide the prime generated from a
previous instance, you can pass it in with `multiplier=`. This value has to be an odd
integer.

```python
from obfuskey import ObfusKey, alphabets


obfuscator = ObfusKey(alphabets.BASE62, multiplier=46485)
key = obfuscator.to_key(12345) # 0cpqVJ
```

If you wish to generate a prime not within the golden prime set, you can overwrite the
multiplier with

```python
from obfuskey import ObfusKey, alphabets


obfuscator = ObfusKey(alphabets.BASE62, key_length=3)
key = obfuscator.to_key(123) # 1O9

obfuscator.set_prime_multiplier(1.75)
key = obfuscator.to_key(123) # Fyl
```

## Extras

If you need to obfuscate integers that are larger than 512-bit, you will need to also
have [gmp2][gmpy2] installed.

```text
$ pip install gmpy2

OR

poetry install -E gmpy2
```

[basehash]: https://github.com/bnlucas/python-basehash
[gmpy2]: https://pypi.org/project/gmpy2/
[pypi]: https://pypi.python.org/pypi/obfuskey
[pypi-v]: https://img.shields.io/pypi/v/obfuskey.svg
[pypi-l]: https://img.shields.io/pypi/l/obfuskey.svg
[codecov]: https://codecov.io/gh/bnlucas/obfuskey
[codecov-i]: https://img.shields.io/codecov/c/github/bnlucas/obfuskey/master.svg
[workflow]: https://github.com/bnlucas/obfuskey/actions?query=branch%3Amain+
[workflow-i]: https://img.shields.io/github/workflow/status/bnlucas/obfuskey/CI/main