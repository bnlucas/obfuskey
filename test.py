from __future__ import annotations

import datetime
import math
import uuid
from typing import Dict, List, Optional, Union, TYPE_CHECKING

# Assuming these are available from your obfuskey package
from obfuskey import Obfuskey, Obfusbit
from obfuskey._constants import KEY_LENGTH
from obfuskey.alphabets import BASE58
from obfuskey.exceptions import BitOverflowError, MaximumValueError, KeyLengthError, UnknownKeyError

# --- Obfusbit Class (for reference, assume this is the one from your last paste) ---
# (Omitted for brevity, as it's provided in the prompt and remains unchanged for this test)
# class Obfusbit: ...

# --- Test Script ---
print("--- Obfuskey and Obfusbit Test Script ---")
print(f"Current Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT')}\n")


# 1. Initialize Obfuskey (for obfuscation)
# Using BASE58 (Bitcoin-style) and a key_length of 12
obk = Obfuskey(BASE58, key_length=12)
print(f"Obfuskey instance initialized:")
print(f"  Alphabet: {obk.alphabet}")
print(f"  Base: {len(obk.alphabet)}")
print(f"  Key Length: {obk.key_length}")
print(f"  Maximum Value Obfuskey can handle: {obk.maximum_value}")
print(f"  Maximum Value Obfuskey can handle (bits): {obk.maximum_value.bit_length()} bits\n")

# 2. Define a schema for Obfusbit (small example)
schema_definition_small = [
    {"name": "user_id", "bits": 20},
    {"name": "product_category", "bits": 4},
    {"name": "status_flag", "bits": 1},
]
obb = Obfusbit(schema_definition_small, obfuskey=obk)
print(f"Obfusbit instance initialized with small schema:")
print(f"  Schema: {obb.schema}")
print(f"  Total bits in schema: {obb.total_bits}")
print(f"  Max packed integer value for schema: {obb.max_bits}\n")

# (Previous Test Cases 1-7 would go here, omitting for brevity to focus on new test)

# --- NEW Test Case: Schema with UUID and More Data (Expected Failure with Small Obfuskey) ---
print("--- Test Case 8: Schema with UUID and More Data (Expected Failure with Small Obfuskey) ---")

# Define schema including UUID (128 bits) and new fields
uuid_complex_schema = [
    {"name": "entity_uuid", "bits": 128},
    {"name": "version", "bits": 4}, # Max 15
    {"name": "creation_day_of_year", "bits": 9}, # Max 366 (2^9 - 1 = 511)
    {"name": "environment_type", "bits": 2}, # Max 3 (e.g., Dev=0, Staging=1, Prod=2, Test=3)
    {"name": "is_active_flag", "bits": 1}, # Max 1 (boolean)
]

# Calculate total bits for this new schema
total_uuid_complex_bits = sum(item["bits"] for item in uuid_complex_schema)
max_uuid_complex_value = (1 << total_uuid_complex_bits) - 1

print(f"Complex UUID schema defined. Total bits required: {total_uuid_complex_bits}.")
print(f"Max packed integer value for complex UUID schema: {max_uuid_complex_value}.")
print(f"The current `obk` instance has a max capacity of {obk.maximum_value.bit_length()} bits ({obk.maximum_value}).\n")

try:
    # This should fail because obk (71 bits capacity) cannot handle 144 bits.
    obb_uuid_complex_fail = Obfusbit(uuid_complex_schema, obfuskey=obk)
    print("ERROR: Expected MaximumValueError during Obfusbit init with complex UUID schema, but no error occurred.")
except MaximumValueError as e:
    print(f"SUCCESS: Caught expected error during Obfusbit init (Complex UUID schema exceeds Obfuskey capacity):\n  {e}\n")
except Exception as e:
    print(f"Caught unexpected error type during Obfusbit init: {type(e).__name__}: {e}\n")


# --- Test Case 9: UUID Schema with More Data and Sufficiently Large Obfuskey (Expected Success) ---
print("--- Test Case 9: UUID Schema with More Data and Sufficiently Large Obfuskey (Expected Success) ---")

# To handle 144 bits with BASE58, we need key_length=25 (24.58 needed, so 25 is minimum).
# Let's use key_length=26 to give it a comfortable margin.
obk_large_capacity_complex = Obfuskey(BASE58, key_length=26)
print(f"Large capacity Obfuskey instance initialized for complex UUID schema:")
print(f"  Key Length: {obk_large_capacity_complex.key_length}")
print(f"  Maximum Value: {obk_large_capacity_complex.maximum_value}")
print(f"  Maximum Value (bits): {obk_large_capacity_complex.maximum_value.bit_length()} bits\n") # Should be >= 144 bits

try:
    # This Obfusbit initialization should now succeed
    obb_uuid_complex_success = Obfusbit(uuid_complex_schema, obfuskey=obk_large_capacity_complex)
    print("Obfusbit instance initialized successfully with complex UUID schema and large Obfuskey capacity.\n")

    # Prepare values to pack for the complex UUID schema
    test_uuid = uuid.uuid4()
    test_uuid_int = test_uuid.int
    test_version = 15
    test_creation_day = 205 # A day in July
    test_environment = 2 # Production
    test_is_active = 1 # True

    values_to_pack_uuid_complex = {
        "entity_uuid": test_uuid_int,
        "version": test_version,
        "creation_day_of_year": test_creation_day,
        "environment_type": test_environment,
        "is_active_flag": test_is_active,
    }
    print(f"Values to pack:")
    for k, v in values_to_pack_uuid_complex.items():
        print(f"  {k}: {v}")
    print(f"(UUID as int: {test_uuid_int})\n")

    # Pack and obfuscate the values
    obfuscated_uuid_code_complex = obb_uuid_complex_success.pack(values_to_pack_uuid_complex, obfuscate=True)
    print(f"Packed and obfuscated complex UUID code: {obfuscated_uuid_code_complex}")
    print(f"Length of code: {len(obfuscated_uuid_code_complex)}")
    print(f"Type of code: {type(obfuscated_uuid_code_complex).__name__}\n")

    # Unpack and de-obfuscate
    unpacked_uuid_complex_values = obb_uuid_complex_success.unpack(obfuscated_uuid_code_complex, obfuscated=True)
    print(f"Unpacked values: {unpacked_uuid_complex_values}")

    # Convert the unpacked integer back to a UUID object for verification
    reconstructed_uuid_int = unpacked_uuid_complex_values["entity_uuid"]
    reconstructed_uuid = uuid.UUID(int=reconstructed_uuid_int)

    # Perform assertions
    print("\n--- Verification ---")
    print(f"Original UUID: {test_uuid}")
    print(f"Reconstructed UUID: {reconstructed_uuid}")
    assert reconstructed_uuid == test_uuid
    print("UUID assertion passed.")

    print(f"Original Version: {test_version}, Reconstructed: {unpacked_uuid_complex_values['version']}")
    assert unpacked_uuid_complex_values["version"] == test_version
    print("Version assertion passed.")

    print(f"Original Day: {test_creation_day}, Reconstructed: {unpacked_uuid_complex_values['creation_day_of_year']}")
    assert unpacked_uuid_complex_values["creation_day_of_year"] == test_creation_day
    print("Creation Day assertion passed.")

    print(f"Original Environment: {test_environment}, Reconstructed: {unpacked_uuid_complex_values['environment_type']}")
    assert unpacked_uuid_complex_values["environment_type"] == test_environment
    print("Environment Type assertion passed.")

    print(f"Original Active Flag: {test_is_active}, Reconstructed: {unpacked_uuid_complex_values['is_active_flag']}")
    assert unpacked_uuid_complex_values["is_active_flag"] == test_is_active
    print("Active Flag assertion passed.\n")

    print("All assertions for complex UUID test passed.\n")

except (BitOverflowError, MaximumValueError, ValueError, TypeError, KeyLengthError, UnknownKeyError) as e:
    print(f"An error occurred during complex UUID packing/unpacking: {e}\n")
except Exception as e:
    print(f"An unexpected error occurred: {type(e).__name__}: {e}\n")

print("--- Test Script End ---")
