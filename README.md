# Obfuskey

[![pypi][pypi-v]][pypi] [![license][pypi-l]][pypi] [![coverage][codecov-i]][codecov] [![build][workflow-i]][workflow]

Taking lessons learned from supporting [BaseHash][basehash] over the years, it was
obvious that it could be optimized, thus Obfuskey was born. BaseHash had some
misconceptions, mainly that consumers thought it was a crypto library due to the word
"hash". Since a hashes are generally irreversible, this new project was born to clearly
convey what it is used for.

Obfuskey was a way to both modernize and simplify [BaseHash][basehash], while keeping
the same functionality. Obfuskey generates obfuscated keys out of integer values that
have a uniform length using a specified alphabet.

**With the release of v0.2.0, Obfuskey now requires Python 3.9 and up.** This version introduces
the `Obfusbit` class for packing multiple values.
**If you need to use Python 3.6, 3.7, or 3.8, you can still use `Obfuskey`'s original
functionality by pinning to version `0.1.3` in your project dependencies.**

When generating keys, the combination of key length and alphabet used will determine the
maximum value it can obfuscate, `len(alphabet) ** key_length - 1`.

## Usage - Obfuskey

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

## Usage - Obfusbit (v0.2.0+)

Obfusbit allows you to pack multiple integer values into a single obfuscated key string.
You define a schema where each field has a name and a specified number of bits. Obfusbit
will combine these values into a single large integer, which can then be obfuscated by
an `Obfuskey` instance. This is ideal for compact identifiers that encode multiple pieces
of information.

### Basic Packing and Unpacking

Define your schema and pack/unpack integers.

```python
from obfuskey import Obfuskey, Obfusbit

# Define your data schema with field names and bit lengths
product_schema = [
    {"name": "category_id", "bits": 4},  # Max value 15
    {"name": "item_id", "bits": 20},     # Max value ~1 million
    {"name": "status", "bits": 3},       # Max value 7 (e.g., in_stock=0, low=1, out=2)
]

# Initialize Obfusbit without an Obfuskey instance if you only need the raw integer
# (e.g., for storage in a database)
obb_int_packer = Obfusbit(product_schema)

# Values to pack (must be within the bit limits)
values_to_pack = {
    "category_id": 5,
    "item_id": 123456,
    "status": 1, # Low stock
}

# Pack into a single integer
packed_id_int = obb_int_packer.pack(values_to_pack, obfuscate=False)
print(f"Packed Integer ID: {packed_id_int}") # e.g., 809492485

# Unpack back to original values
unpacked_values = obb_int_packer.unpack(packed_id_int, obfuscated=False)
print(f"Unpacked values: {unpacked_values}")
# Output: {'status': 1, 'item_id': 123456, 'category_id': 5}
```

### Determining Alphabet and Key Length

When using `Obfusbit` with an `Obfuskey` instance for obfuscation, it's crucial that the
`Obfuskey` is configured to handle the maximum possible integer value that your schema
can produce.

1.  **Calculate Total Bits Required by Schema:** Sum the `bits` for all fields in your
    `Obfusbit` schema. This sum represents the total number of bits needed to represent
    the packed integer.
    - Example: `[{"bits": 4}, {"bits": 20}, {"bits": 3}]` = `4 + 20 + 3 = 27` total bits.
2.  **Calculate Maximum Value Represented by Schema:** The maximum integer value your
    schema can pack is `(2 ** total_bits) - 1`.
    - Example: For 27 total bits, the maximum value is `(2 ** 27) - 1 = 134,217,727`.
3.  **Determine `Obfuskey` Capacity:** The maximum value an `Obfuskey` instance can obfuscate
    is determined by its alphabet size and key length: `(len(alphabet) ** key_length) - 1`.
    - Example: Using `BASE58` (alphabet size 58) with `key_length=5` gives
      `(58 ** 5) - 1 = 656,356,799`.

**The `Obfuskey`'s maximum capacity MUST be greater than or equal to the maximum value your
schema can produce.** If it's smaller, `Obfusbit` will raise a `MaximumValueError` during 
`pack` or initialization.

**Tips for Choosing:**

- **`total_bits`:** This is fixed by your schema requirements.
- **`alphabet`:**
  - **Smaller alphabets** (e.g., `BASE16`, `BASE36`) result in longer keys for the same
    `total_bits`. They are often easier to type or read.
  - **Larger alphabets** (e.g., `BASE58`, `BASE62`, `BASE64`, `BASE94`) result in shorter,
    more compact keys for the same `total_bits`. They might be less human-friendly but more
    efficient.
- **`key_length`:** This is derived from your `total_bits` and chosen `alphabet`. You need
  to find the smallest `key_length` such that `(len(alphabet) ** key_length) - 1` covers
  your `(2 ** total_bits) - 1`.
  - A good rule of thumb is to take `ceil(total_bits / log2(alphabet_size))` to estimate the
    required key length (where `log2` is log base 2), but often a bit of trial and error
    (or using the `MaximumValueError` to guide you) is practical.
  - **Example from below (144 bits):** For `BASE58` (alphabet size 58, which is approximately
    2^5.85), you need roughly `144 / 5.85` which is about `24.6` characters. So, a `key_length`
    of 25 would likely be the minimum, and 26 is used for safety in the example.

### Packing and Unpacking with Obfuscation

To get a human-readable, fixed-length obfuscated key string, you associate an `Obfuskey`
instance with `Obfusbit`. Ensure the `Obfuskey`'s `maximum_value` is large enough to
cover the total bits in your schema.

```python
import datetime
import uuid
from obfuskey import Obfuskey, Obfusbit, alphabets

# Define a more complex schema, including a UUID
# UUIDs are 128-bit numbers.
complex_id_schema = [
    {"name": "entity_uuid", "bits": 128},
    {"name": "version", "bits": 4},           # e.g., schema version
    {"name": "creation_day", "bits": 9},      # Day of the year (1-366)
    {"name": "environment_id", "bits": 2},    # e.g., 0=Dev, 1=Staging, 2=Prod
    {"name": "is_active", "bits": 1},         # Boolean flag
]

# Calculate required bits: 128 + 4 + 9 + 2 + 1 = 144 bits.
# For BASE58 (base 58), 58^25 is roughly 2^144. Use key_length=26 for safety.
obfuscator_large = Obfuskey(alphabets.BASE58, key_length=26)

# Initialize Obfusbit with the schema and the Obfuskey instance
obb_obfuscated_packer = Obfusbit(complex_id_schema, obfuskey=obfuscator_large)

# Prepare values for packing
current_uuid = uuid.uuid4()
current_day_of_year = datetime.datetime.now().timetuple().tm_yday

values_to_pack_complex = {
    "entity_uuid": current_uuid.int, # Convert UUID object to its 128-bit integer
    "version": 1,
    "creation_day": current_day_of_year,
    "environment_id": 2, # Production
    "is_active": 1, # True
}

# Pack and obfuscate into a string
obfuscated_code = obb_obfuscated_packer.pack(values_to_pack_complex, obfuscate=True)
print(f"Obfuscated Complex ID: {obfuscated_code}") # e.g., T6ATbW8QpS3qBVACGganMCi4rU

# Unpack and de-obfuscate
unpacked_complex_values = obb_obfuscated_packer.unpack(obfuscated_code, obfuscated=True)
print(f"Unpacked Complex Values: {unpacked_complex_values}")

# Convert the UUID integer back to a UUID object for verification
reconstructed_uuid = uuid.UUID(int=unpacked_complex_values["entity_uuid"])
print(f"Reconstructed UUID: {reconstructed_uuid}")
print(f"Original UUID matches reconstructed: {reconstructed_uuid == current_uuid}")

# This will raise a MaximumValueError if obfuskey_large is too small for the schema.
# This will raise a BitOverflowError if any single value exceeds its allocated bits.
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
