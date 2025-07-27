from __future__ import annotations

from typing import Dict, List, Any, Set

from obfuskey.exceptions import SchemaValidationError


class ObfusbitSchema:
    """
    Represents and validates the schema definition for packing and unpacking integers
    with Obfusbit.

    A schema is a list of dictionaries, where each dictionary defines a field
    with a 'name' (string) and 'bits' (integer). The order of fields in the schema
    determines their position in the packed integer, with the first field occupying
    the least significant bits and subsequent fields occupying higher bits.

    :param raw_schema: A list of dictionaries defining the schema. Each dictionary
                       must have 'name' (str) and 'bits' (int) keys.
    :raises SchemaValidationError: If the provided raw_schema is invalid.
    """

    def __init__(self, raw_schema: List[Dict[str, int]]):
        self._validate_schema(raw_schema)
        self._schema_definition = raw_schema
        self._total_bits_val = sum(item["bits"] for item in raw_schema)
        self._max_bits_val = (1 << self._total_bits_val) - 1
        self._field_info = self._calculate_field_info(raw_schema)

    def __repr__(self) -> str:
        """
        Returns a string representation of the ObfusbitSchema object.
        """
        return f"ObfusbitSchema(total_bits={self.total_bits}, fields={len(self.definition)})"

    @property
    def definition(self) -> List[Dict[str, int]]:
        """
        The raw schema definition list provided during initialization.

        :return: A list of dictionaries representing the schema.
        :rtype: List[Dict[str, int]]
        """
        return self._schema_definition

    @property
    def field_info(self) -> Dict[str, Dict[str, int]]:
        """
        A copy of the pre-calculated information for each field,
        including its allocated 'bits' and its 'shift' position within the packed integer.

        :return: A dictionary where keys are field names (str) and values are
                 dictionaries containing 'bits' and 'shift' (int).
        :rtype: Dict[str, Dict[str, int]]
        """
        return self._field_info.copy()

    @property
    def total_bits(self) -> int:
        """
        The total number of bits required to pack all fields defined in the schema.

        :return: The total number of bits.
        :rtype: int
        """
        return self._total_bits_val

    @property
    def max_bits(self) -> int:
        """
        The maximum possible integer value that can be represented by this schema's
        total bit capacity. This is (2^total_bits) - 1.

        :return: The maximum integer value.
        :rtype: int
        """
        return self._max_bits_val

    @staticmethod
    def _calculate_field_info(
        raw_schema: List[Dict[str, int]],
    ) -> Dict[str, Dict[str, int]]:
        """
        Calculates and stores bits and bit shifts for each field for quick lookup
        during packing and unpacking. This is a static method as it operates solely
        on the raw_schema input.

        :param raw_schema: The list of dictionaries defining the schema.
        :return: A dictionary mapping field names to dictionaries containing 'bits' and 'shift'.
        :rtype: Dict[str, Dict[str, int]]
        """
        field_info = {}
        current_shift = 0

        # Fields are packed from least significant to most significant bits.
        # Iterating in reverse calculates the correct shift for each field
        # based on the cumulative bit length of subsequent fields.
        for item in reversed(raw_schema):
            field_info[str(item["name"])] = {
                "bits": item["bits"],
                "shift": current_shift,
            }
            current_shift += item["bits"]

        return field_info

    @staticmethod
    def _validate_schema_item(
        item: Dict[str, Any],
        index: int,
        seen_names: Set[str],
    ) -> None:
        """
        Validates a single dictionary item within the schema list.
        This is a static method as it operates on the item and provided context.

        :param item: The dictionary representing a single field definition.
        :param index: The index of the item within the schema list (for error reporting).
        :param seen_names: A set of field names encountered so far (for duplicate checking).
        :raises SchemaValidationError: If the schema item is invalid.
        """
        if not isinstance(item, dict):
            raise SchemaValidationError(
                f"Schema item at index {index} must be a dictionary, got {type(item).__name__}."
            )

        if "name" not in item:
            raise SchemaValidationError(
                f"Schema item at index {index} is missing the 'name' key."
            )
        if "bits" not in item:
            raise SchemaValidationError(
                f"Schema item at index {index} is missing the 'bits' key."
            )

        name = item["name"]
        bits = item["bits"]

        if not isinstance(name, str):
            raise SchemaValidationError(
                f"Schema item (index {index}): 'name' must be a string, got {type(name).__name__}."
            )
        if not isinstance(bits, int):
            raise SchemaValidationError(
                f"Schema item '{name}' (index {index}): 'bits' must be an integer, got {type(bits).__name__}."
            )

        if bits <= 0:
            raise SchemaValidationError(
                f"Schema item '{name}' (index {index}): 'bits' must be a positive integer, got {bits}."
            )

        if name in seen_names:
            raise SchemaValidationError(
                f"Schema contains duplicate name: '{name}'. Names must be unique."
            )

    def _validate_schema(
        self,
        schema: List[Dict[str, int]],
    ) -> None:
        """
        Validates the overall structure of the schema list (e.g., non-empty, correct type)
        and iterates through items, delegating individual item validation to `_validate_schema_item`.

        :param schema: The raw schema list to be validated.
        :raises SchemaValidationError: If the schema list or any of its items are invalid.
        """
        if not isinstance(schema, list):
            raise SchemaValidationError("Schema must be a list of dictionaries.")

        if not schema:
            raise SchemaValidationError("Schema cannot be empty.")

        seen_names: Set[str] = set()

        for i, item in enumerate(schema):
            self._validate_schema_item(item, i, seen_names)
            seen_names.add(str(item["name"]))

    def get_field_info(self, name: str) -> Dict[str, int]:
        """
        Returns a dictionary containing 'bits' and 'shift' for a specific field name.

        :param name: The name of the field to retrieve information for.
        :return: A dictionary with 'bits' (int) and 'shift' (int) for the specified field.
        :raises ValueError: If the field name is not found in the schema.
        :rtype: Dict[str, int]
        """
        if name not in self._field_info:
            raise ValueError(f"Field '{name}' not found in schema.")
        return self._field_info[name]


__all__ = ("ObfusbitSchema",)
