# Obfuskey

[![pypi][pypi-v]][pypi] [![license][pypi-l]][pypi] [![coverage][codecov-i]][codecov] [![build][workflow-i]][workflow]

Taking lessons learned from supporting [BaseHash][basehash] over the years, it was
obvious that it could be optimized, thus Obfuskey was born. BaseHash had some
misconceptions, mainly that consumers thought it was a crypto library due to the word 
"hash". Since a hashes are generally irreversible, this new project was born to clearly 
convey what it is used for.

Obfuskey was a way to both modernize and simplify [BaseHash][basehash], while keeping
the same functionality. Obfuskey generates obfuscated keys out of integer values that
have a uniform length using a specified alphabet. It was built solely for Python 3.6 and
up. There are no guarantees that it will work for lower versions. If you need this for
a lower version, please use [BaseHash][basehash].

When generating keys, the combination of key length and alphabet used will determine the
maximum value it can obfuscate, `len(alphabet) ** key_length - 1`.

## Usage

To use Obfuskey, you can use one of the available alphabets, or provide your own. You
can also provide your own multiplier, or leave it blank to use the built-in prime
generator.

```python
from obfuskey import Obfuskey, alphabets

obfuscator = Obfuskey(alphabets.BASE36, key_length=8)

key = obfuscator.get_key(1234567890)  # FWQ8H52I
value = obfuscator.get_value('FWQ8H52I')  # 1234567890
```

To provide a custom multiplier, or if you to provide the prime generated from a
previous instance, you can pass it in with `multiplier=`. This value has to be an odd
integer.

```python
from obfuskey import Obfuskey, alphabets

obfuscator = Obfuskey(alphabets.BASE62)
key = obfuscator.get_key(12345)  # d2Aasl

obfuscator = Obfuskey(alphabets.BASE62, multiplier=46485)
key = obfuscator.get_key(12345)  # 0cpqVJ
```

If you wish to generate a prime not within the golden prime set, you can overwrite the
multiplier with `set_prime_multiplier`.

```python
from obfuskey import Obfuskey, alphabets

obfuscator = Obfuskey(alphabets.BASE62, key_length=2)
key = obfuscator.get_key(123)  # 3f

obfuscator.set_prime_multiplier(1.75)
key = obfuscator.get_key(123)  # RP
```

There are predefined [alphabets][alphabets] that you can use, but Obfuskey allows you to
specify a custom one during instantiation.

```python
from obfuskey import Obfuskey

obfuscator = Obfuskey('012345abcdef')
key = obfuscator.get_key(123) #022d43
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
[alphabets]: https://github.com/bnlucas/obfuskey/blob/main/obfuskey/alphabets.py
[gmpy2]: https://pypi.org/project/gmpy2/
[pypi]: https://pypi.python.org/pypi/Obfuskey
[pypi-v]: https://img.shields.io/pypi/v/Obfuskey.svg
[pypi-l]: https://img.shields.io/pypi/l/Obfuskey.svg
[codecov]: https://codecov.io/gh/bnlucas/Obfuskey
[codecov-i]: https://img.shields.io/codecov/c/github/bnlucas/Obfuskey/master.svg
[workflow]: https://github.com/bnlucas/Obfuskey/actions?query=branch%3Amain+
[workflow-i]: https://img.shields.io/github/workflow/status/bnlucas/Obfuskey/CI/main