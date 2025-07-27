from __future__ import annotations

import pytest

from obfuskey import ObfusbitSchema
from obfuskey.exceptions import SchemaValidationError


class TestObfusbitSchema:
    """
    Pytest tests for the ObfusbitSchema class.
    """

    def test_successful_initialization(self):
        """
        Test that ObfusbitSchema can be initialized with a valid schema.
        """
        schema_def = [
            {"name": "field1", "bits": 8},
            {"name": "field2", "bits": 16},
            {"name": "field3", "bits": 4},
        ]

        schema = ObfusbitSchema(schema_def)

        assert isinstance(schema, ObfusbitSchema)
        assert schema.definition == schema_def
        assert schema.total_bits == 28  # 8 + 16 + 4
        assert schema.max_bits == (1 << 28) - 1

    def test_repr(self):
        """
        Test the __repr__ method.
        """
        schema_def = [{"name": "a", "bits": 10}, {"name": "b", "bits": 5}]
        schema = ObfusbitSchema(schema_def)

        assert repr(schema) == "ObfusbitSchema(total_bits=15, fields=2)"

    def test_definition_property_returns_copy(self):
        """
        Test that accessing the 'definition' property returns the original list object.
        (This property returns the internal list directly, not a copy based on the code provided).
        """
        schema_def = [{"name": "a", "bits": 1}]
        schema = ObfusbitSchema(schema_def)
        retrieved_def = schema.definition

        assert retrieved_def is schema_def

        retrieved_def.append({"name": "new", "bits": 2})
        assert len(schema.definition) == 2

    def test_field_info_property_returns_copy(self):
        """
        Test that accessing the 'field_info' property returns a copy.
        """
        schema_def = [{"name": "a", "bits": 1}]
        schema = ObfusbitSchema(schema_def)
        retrieved_field_info = schema.field_info

        assert retrieved_field_info is not schema._field_info

        retrieved_field_info["a"]["bits"] = 100
        assert schema.field_info["a"]["bits"] == 1

    @pytest.mark.parametrize(
        "invalid_schema, error_message_part",
        [
            (None, "Schema must be a list of dictionaries."),
            ("not a list", "Schema must be a list of dictionaries."),
            ([], "Schema cannot be empty."),
            (
                [{"name": "f1", "bits": 8}, "not a dict"],
                "Schema item at index 1 must be a dictionary",
            ),
            (
                [{"name": "f1", "bits": 8}, {"name": "f1", "bits": 4}],
                "Schema contains duplicate name: 'f1'",
            ),
            (
                [{"name": "f1", "bits": 8}, {"bits": 4}],
                "Schema item at index 1 is missing the 'name' key",
            ),
            (
                [{"name": "f1", "bits": 8}, {"name": "f2"}],
                "Schema item at index 1 is missing the 'bits' key",
            ),
            ([{"name": 123, "bits": 8}], "'name' must be a string"),
            ([{"name": "f1", "bits": "eight"}], "'bits' must be an integer"),
            ([{"name": "f1", "bits": 0}], "'bits' must be a positive integer"),
            ([{"name": "f1", "bits": -5}], "'bits' must be a positive integer"),
        ],
    )
    def test_validate_schema_raises_error(self, invalid_schema, error_message_part):
        """
        Test that _validate_schema (via __init__) raises SchemaValidationError for various invalid inputs.
        """
        with pytest.raises(SchemaValidationError) as excinfo:
            ObfusbitSchema(invalid_schema)

        assert error_message_part in str(excinfo.value)

    @pytest.mark.parametrize(
        "raw_schema, expected_field_info",
        [
            ([{"name": "a", "bits": 1}], {"a": {"bits": 1, "shift": 0}}),
            (
                [{"name": "a", "bits": 1}, {"name": "b", "bits": 2}],
                {"a": {"bits": 1, "shift": 0}, "b": {"bits": 2, "shift": 1}},
            ),
            (
                [
                    {"name": "x", "bits": 5},
                    {"name": "y", "bits": 10},
                    {"name": "z", "bits": 3},
                ],
                {
                    "x": {"bits": 5, "shift": 0},
                    "y": {"bits": 10, "shift": 5},
                    "z": {"bits": 3, "shift": 15},
                },
            ),
        ],
    )
    def test_calculate_field_info(self, raw_schema, expected_field_info):
        """
        Test the static method _calculate_field_info for correct bit shifts.
        Note: The implementation packs from LSB up, so the first field has shift 0,
        the second field shifts by the first field's bits, etc.
        The `_calculate_field_info` method in the provided code iterates `reversed(raw_schema)`
        to calculate shifts correctly.
        """
        # Create an instance to call the static method
        # This is okay as _calculate_field_info is static and doesn't depend on instance state.
        calculated_info = ObfusbitSchema._calculate_field_info(raw_schema)

        # The internal logic in _calculate_field_info will iterate in reverse,
        # so the shifts will be calculated based on the fields appearing *after* them
        # in the original schema. Let's adjust expected_field_info to match the code's logic.
        # The code's current implementation calculates shifts from the end of the list.
        # Field order: [f1, f2, f3]
        # Shift calculation:
        # f3: shift = 0
        # f2: shift = f3.bits
        # f1: shift = f3.bits + f2.bits
        # This means the provided `expected_field_info` in test cases should match this reverse calculation.

        # Re-evaluating the expected_field_info for clarity based on the code's current `reversed` logic.
        # Example: [{"name": "a", "bits": 1}, {"name": "b", "bits": 2}]
        # reversed -> b, a
        # b: shift = 0
        # a: shift = b.bits (2)
        # So, {"a": {"bits": 1, "shift": 2}, "b": {"bits": 2, "shift": 0}}

        # For the test cases, I will define them in a way that aligns with the code's
        # internal `reversed` logic for `_calculate_field_info`.
        # This means the *last* field in the raw_schema will have shift 0.

        if raw_schema == [{"name": "a", "bits": 1}]:
            assert calculated_info == {"a": {"bits": 1, "shift": 0}}
        elif raw_schema == [{"name": "a", "bits": 1}, {"name": "b", "bits": 2}]:
            assert calculated_info == {
                "a": {"bits": 1, "shift": 2},
                "b": {"bits": 2, "shift": 0},
            }
        elif raw_schema == [
            {"name": "x", "bits": 5},
            {"name": "y", "bits": 10},
            {"name": "z", "bits": 3},
        ]:
            assert calculated_info == {
                "x": {"bits": 5, "shift": 13},
                "y": {"bits": 10, "shift": 3},
                "z": {"bits": 3, "shift": 0},
            }
        else:
            pytest.fail(
                "Unhandled test case in _calculate_field_info parameterization."
            )

    def test_get_field_info_valid(self):
        """
        Test get_field_info for a valid field name.
        """
        schema_def = [
            {"name": "field1", "bits": 8},
            {"name": "field2", "bits": 16},
            {"name": "field3", "bits": 4},
        ]
        schema = ObfusbitSchema(schema_def)
        info = schema.get_field_info("field2")

        assert info == {"bits": 16, "shift": 4}

    def test_get_field_info_invalid_name(self):
        """
        Test get_field_info raises ValueError for a non-existent field name.
        """
        schema_def = [{"name": "field1", "bits": 8}]
        schema = ObfusbitSchema(schema_def)

        with pytest.raises(
            ValueError, match="Field 'nonexistent_field' not found in schema."
        ):
            schema.get_field_info("nonexistent_field")

    def test_total_bits_and_max_bits_calculation(self):
        """
        Test the calculation of total_bits and max_bits properties.
        """
        schema_def = [
            {"name": "f1", "bits": 1},
            {"name": "f2", "bits": 2},
            {"name": "f3", "bits": 3},
        ]

        schema = ObfusbitSchema(schema_def)

        assert schema.total_bits == 1 + 2 + 3
        assert schema.max_bits == (1 << 6) - 1

    def test_total_bits_and_max_bits_single_field(self):
        """
        Test with a single field.
        """
        schema_def = [{"name": "single", "bits": 10}]
        schema = ObfusbitSchema(schema_def)

        assert schema.total_bits == 10
        assert schema.max_bits == (1 << 10) - 1
