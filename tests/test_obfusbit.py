from __future__ import annotations

import pytest
import uuid
import datetime

from typing import Dict, List, Union

from obfuskey import Obfuskey, Obfusbit, alphabets
from obfuskey.exceptions import (
    BitOverflowError,
    MaximumValueError,
    KeyLengthError,
    UnknownKeyError,
)


@pytest.fixture
def small_schema() -> List[Dict[str, int]]:
    """A small schema for basic testing."""
    return [
        {"name": "field_a", "bits": 8},  # Max 255
        {"name": "field_b", "bits": 4},  # Max 15
        {"name": "flag_c", "bits": 1},  # Max 1
    ]  # Total 13 bits, Max packed value = 2^13 - 1 = 8191


@pytest.fixture
def obfuskey_for_small_schema() -> Obfuskey:
    """Obfuskey instance sufficient for small_schema (e.g., 13 bits)."""
    # BASE58, key_length=6 => max_value ~4e10 (covers 13 bits easily)
    return Obfuskey(alphabets.BASE58, key_length=6)


@pytest.fixture
def complex_uuid_schema() -> List[Dict[str, int]]:
    """A schema that includes a UUID and other fields."""
    return [
        {"name": "entity_uuid", "bits": 128},
        {"name": "version", "bits": 4},
        {"name": "creation_day_of_year", "bits": 9},
        {"name": "environment_type", "bits": 2},
        {"name": "is_active_flag", "bits": 1},
    ]  # Total 144 bits


@pytest.fixture
def obfuskey_for_complex_uuid_schema() -> Obfuskey:
    """Obfuskey instance sufficient for complex_uuid_schema (144 bits)."""
    # Need key_length at least 25 for BASE58 to cover 144 bits. Use 26 for safety.
    return Obfuskey(alphabets.BASE58, key_length=26)


@pytest.fixture
def obfuskey_too_small_for_uuid() -> Obfuskey:
    """Obfuskey instance that cannot handle a UUID's bit length."""
    return Obfuskey(
        alphabets.BASE58, key_length=12
    )  # Max ~71 bits, much smaller than 144 bits


class TestObfusbit:

    def test_obfusbit_init_no_obfuskey(
        self,
        small_schema: List[Dict[str, int]],
    ) -> None:
        """Test Obfusbit initialization without an Obfuskey instance."""
        obb = Obfusbit(small_schema)
        assert obb.schema == small_schema
        assert obb.obfuskey is None
        assert obb.total_bits == 13
        assert obb.max_bits == (1 << 13) - 1

    def test_obfusbit_init_with_obfuskey(
        self,
        small_schema: List[Dict[str, int]],
        obfuskey_for_small_schema: Obfuskey,
    ) -> None:
        """Test Obfusbit initialization with an Obfuskey instance."""
        obb = Obfusbit(small_schema, obfuskey=obfuskey_for_small_schema)

        assert obb.schema == small_schema
        assert obb.obfuskey == obfuskey_for_small_schema
        assert obb.total_bits == 13

    def test_obfusbit_init_schema_exceeds_obfuskey_max(
        self,
        complex_uuid_schema: List[Dict[str, int]],
        obfuskey_too_small_for_uuid: Obfuskey,
    ) -> None:
        """
        Test that Obfusbit initialization fails if the schema's max packed value
        exceeds the provided Obfuskey's maximum_value.
        """
        # Debugging check: Ensure fixture logic is sound for this test
        total_schema_bits = sum(item["bits"] for item in complex_uuid_schema)
        schema_max_packed_value = (1 << total_schema_bits) - 1
        assert (
            obfuskey_too_small_for_uuid.maximum_value < schema_max_packed_value
        ), "Fixture obfuskey_too_small_for_uuid is not small enough for complex_uuid_schema!"

        with pytest.raises(MaximumValueError) as excinfo:
            Obfusbit(complex_uuid_schema, obfuskey=obfuskey_too_small_for_uuid)

        # Check parts of the error message for robustness
        assert "The provided schema requires a maximum packed integer value of" in str(
            excinfo.value
        )

        assert (
            "but the provided Obfuskey instance can only handle up to a maximum value of"
            in str(excinfo.value)
        )

    def test_pack_and_unpack_no_obfuscation(
        self,
        small_schema: List[Dict[str, int]],
    ) -> None:
        """Test packing and unpacking without obfuscation (raw integer)."""
        obb = Obfusbit(small_schema)

        expected_values = {
            "field_a": 123,  # Fits in 8 bits (0-255)
            "field_b": 7,  # Fits in 4 bits (0-15)
            "flag_c": 1,  # Fits in 1 bit (0-1)
        }

        packed_int = obb.pack(expected_values, obfuscate=False)
        assert isinstance(packed_int, int)

        actual_values = obb.unpack(packed_int, obfuscated=False)
        assert actual_values == expected_values

    def test_pack_and_unpack_with_obfuscation(
        self,
        small_schema: List[Dict[str, int]],
        obfuskey_for_small_schema: Obfuskey,
    ) -> None:
        """Test packing and unpacking with obfuscation (string key)."""
        obb = Obfusbit(small_schema, obfuskey=obfuskey_for_small_schema)

        expected_values = {
            "field_a": 200,
            "field_b": 10,
            "flag_c": 0,
        }

        obfuscated_key = obb.pack(expected_values, obfuscate=True)
        assert isinstance(obfuscated_key, str)
        assert len(obfuscated_key) == obfuskey_for_small_schema.key_length

        actual_values = obb.unpack(obfuscated_key, obfuscated=True)
        assert actual_values == expected_values

    def test_pack_bit_overflow_error(
        self,
        small_schema: List[Dict[str, int]],
    ) -> None:
        """Test that packing raises BitOverflowError for values exceeding allocated bits."""
        obb = Obfusbit(small_schema)

        invalid_values = {
            "field_a": 256,  # Exceeds 8 bits (max 255)
            "field_b": 5,
            "flag_c": 0,
        }

        with pytest.raises(BitOverflowError) as excinfo:
            obb.pack(invalid_values)

        assert "exceeds its allocated" in str(excinfo.value)
        assert "field_a" in str(excinfo.value)

    def test_pack_missing_value_error(
        self,
        small_schema: List[Dict[str, int]],
    ) -> None:
        """Test that packing raises ValueError for missing required values."""
        obb = Obfusbit(small_schema)

        invalid_values = {
            "field_a": 10,
            # "field_b" is missing
            "flag_c": 0,
        }

        with pytest.raises(ValueError) as excinfo:
            obb.pack(invalid_values)

        assert "Required value for 'field_b' not provided" in str(excinfo.value)

    def test_pack_obfuscate_without_obfuskey_error(
        self,
        small_schema: List[Dict[str, int]],
    ) -> None:
        """Test that packing with obfuscate=True fails if Obfuskey is not provided."""
        obb = Obfusbit(small_schema)  # No obfuskey instance

        with pytest.raises(ValueError) as excinfo:
            obb.pack({"field_a": 1, "field_b": 1, "flag_c": 0}, obfuscate=True)

        assert "An Obfuskey instance was not provided" in str(excinfo.value)

    def test_unpack_obfuscated_without_obfuskey_error(
        self,
        small_schema: List[Dict[str, int]],
    ) -> None:
        """Test that unpacking with obfuscated=True fails if Obfuskey is not provided."""
        obb = Obfusbit(small_schema)  # No obfuskey instance

        with pytest.raises(ValueError) as excinfo:
            obb.unpack("some_obfuscated_string", obfuscated=True)

        assert "An Obfuskey instance was not provided" in str(excinfo.value)

    @pytest.mark.parametrize(
        "value, obfuscated, expected_error",
        [
            (12345, True, TypeError),  # Expecting string, got int
            ("invalid_string", False, TypeError),  # Expecting int, got string
        ],
    )
    def test_unpack_type_error(
        self,
        small_schema: List[Dict[str, int]],
        obfuskey_for_small_schema: Obfuskey,
        value: Union[str, int],
        obfuscated: bool,
        expected_error: type[Exception],
    ) -> None:
        """Test that unpack raises TypeError for incorrect input types based on obfuscated flag."""
        obb = Obfusbit(small_schema, obfuskey=obfuskey_for_small_schema)

        with pytest.raises(expected_error) as excinfo:
            obb.unpack(value, obfuscated=obfuscated)

        assert "must be a string" in str(excinfo.value) or "must be an integer" in str(
            excinfo.value
        )

    def test_unpack_obfuskey_errors_passthrough(
        self,
        small_schema: List[Dict[str, int]],
        obfuskey_for_small_schema: Obfuskey,
    ) -> None:
        """Test that Obfuskey-specific errors (UnknownKeyError, KeyLengthError) pass through unpack."""
        obb = Obfusbit(small_schema, obfuskey=obfuskey_for_small_schema)

        # Test UnknownKeyError
        with pytest.raises(UnknownKeyError):
            obb.unpack("!!!!badkey!!", obfuscated=True)  # Contains chars not in BASE58

        # Test KeyLengthError
        with pytest.raises(KeyLengthError):
            obb.unpack("short", obfuscated=True)  # Too short for key_length=6

    def test_uuid_packing_and_unpacking_success(
        self,
        complex_uuid_schema: List[Dict[str, int]],
        obfuskey_for_complex_uuid_schema: Obfuskey,
    ) -> None:
        """Test packing and unpacking a schema containing a UUID and other fields."""
        obb = Obfusbit(complex_uuid_schema, obfuskey=obfuskey_for_complex_uuid_schema)

        test_uuid = uuid.uuid4()
        test_uuid_int = test_uuid.int
        current_day = datetime.datetime.now().timetuple().tm_yday  # Day of year 1-366

        expected_values = {
            "entity_uuid": test_uuid_int,
            "version": 15,
            "creation_day_of_year": current_day,
            "environment_type": 1,  # Staging
            "is_active_flag": 1,
        }

        obfuscated_key = obb.pack(expected_values, obfuscate=True)
        assert isinstance(obfuscated_key, str)
        assert len(obfuscated_key) == obfuskey_for_complex_uuid_schema.key_length

        actual_values = obb.unpack(obfuscated_key, obfuscated=True)

        # Verify all fields
        assert actual_values["entity_uuid"] == expected_values["entity_uuid"]
        assert uuid.UUID(int=actual_values["entity_uuid"]) == test_uuid
        assert actual_values["version"] == expected_values["version"]
        assert (
            actual_values["creation_day_of_year"]
            == expected_values["creation_day_of_year"]
        )
        assert actual_values["environment_type"] == expected_values["environment_type"]
        assert actual_values["is_active_flag"] == expected_values["is_active_flag"]

        # A full dictionary comparison is also good if order doesn't matter
        assert actual_values == expected_values  # This implicitly checks all items
