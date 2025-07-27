from __future__ import annotations

from typing import Dict, List, Union, Optional, Literal

from obfuskey._obfusbit_schema import ObfusbitSchema
from obfuskey._obfuskey import Obfuskey
from obfuskey.exceptions import MaximumValueError


class Obfusbit:
    """
    Obfusbit facilitates the packing and unpacking of multiple integer values
    into a single integer or an obfuscated string, based on a defined schema.

    It allows for efficient storage and transfer of structured data in a compact
    numerical format, with optional obfuscation provided by an Obfuskey instance.
    """

    def __init__(
        self,
        schema: Union[List[Dict[str, int]], ObfusbitSchema],
        *,
        obfuskey: Optional[Obfuskey] = None,
    ):
        """
        Initializes an Obfusbit instance with a schema and an optional Obfuskey.

        :param schema: A list of dictionaries defining the schema, or an
                       existing ObfusbitSchema object.
        :param obfuskey: An optional Obfuskey instance for obfuscating/de-obfuscating
                         the packed integer.
        :raises MaximumValueError: If the provided Obfuskey cannot handle the
                                   maximum possible value representable by the schema.
        :raises SchemaValidationError: If the provided schema definition is invalid.
        """
        if isinstance(schema, ObfusbitSchema):
            self._schema = schema
        else:
            self._schema = ObfusbitSchema(schema)

        self._obfuskey = obfuskey
        self._total_bits = self._schema.total_bits
        self._max_bits = self._schema.max_bits

        if self._obfuskey and self._max_bits > self._obfuskey.maximum_value:
            raise MaximumValueError(
                f"The provided schema requires a maximum packed integer value of {self._max_bits} "
                f"(which needs {self._total_bits} bits to represent), but the provided Obfuskey instance "
                f"can only handle up to a maximum value of {self._obfuskey.maximum_value} "
                f"(which covers {self._obfuskey.maximum_value.bit_length()} bits)."
            )

    def __repr__(self) -> str:
        """
        Returns a string representation of the Obfusbit object.
        """
        obfuskey_repr = f"obfuskey={self.obfuskey}" if self.obfuskey else "no obfuskey"

        return f"Obfusbit(schema={self._schema}, {obfuskey_repr})"

    @property
    def total_bits(self) -> int:
        """
        The total number of bits required by the schema.
        """
        return self._total_bits

    @property
    def max_bits(self) -> int:
        """
        The maximum possible integer value that can be represented by this schema's
        total bit capacity.
        """
        return self._max_bits

    @property
    def schema(self) -> List[Dict[str, int]]:
        """
        A copy of the raw schema definition used by this Obfusbit instance.
        """
        return self._schema.definition

    @property
    def obfuskey(self) -> Optional[Obfuskey]:
        """
        The Obfuskey instance associated with this Obfusbit instance, if any.
        """
        return self._obfuskey

    def _get_required_byte_length(self) -> int:
        """
        Calculates the minimum number of bytes needed to store the total_bits.
        """
        return (self._total_bits + 7) // 8

    def _int_to_bytes_internal(
        self, packed_int: int, byteorder: Literal["little", "big"]
    ) -> bytes:
        """
        Converts a packed integer into a fixed-length byte sequence.

        :param packed_int: The integer to convert.
        :param byteorder: The byte order ('little' or 'big').
        :return: The bytes representation.
        :raises ValueError: If packed_int is out of the schema's range.
        """
        byte_length = self._get_required_byte_length()

        if not (0 <= packed_int <= self._max_bits):
            raise ValueError(
                f"Packed integer {packed_int} is out of range (0 to {self._max_bits}) "
                f"for the schema's total bit capacity."
            )

        return packed_int.to_bytes(byte_length, byteorder=byteorder)

    def _bytes_to_int_internal(
        self, byte_data: bytes, byteorder: Literal["little", "big"]
    ) -> int:
        """
        Converts a byte sequence back into an integer.

        :param byte_data: The bytes to convert.
        :param byteorder: The byte order ('little' or 'big').
        :return: The integer representation.
        :raises TypeError: If byte_data is not a bytes object.
        :raises ValueError: If byte_data length does not match expected length.
        """
        if not isinstance(byte_data, bytes):
            raise TypeError("Input 'byte_data' must be a bytes object.")

        expected_byte_length = self._get_required_byte_length()

        if len(byte_data) != expected_byte_length:
            raise ValueError(
                f"Byte data length ({len(byte_data)}) does not match expected length "
                f"for this schema ({expected_byte_length} bytes based on {self._total_bits} bits)."
            )

        return int.from_bytes(byte_data, byteorder=byteorder)

    def pack(self, values: Dict[str, int], obfuscate: bool = False) -> Union[int, str]:
        """
        Packs a dictionary of values into a single integer or an obfuscated key.

        The input `values` are validated against the schema for missing fields,
        unexpected fields, and individual value bit overflow.

        :param values: A dictionary where keys are field names and values are their integer values.
        :param obfuscate: If True, the packed integer will be obfuscated using the
                          Obfuskey instance (if provided during initialization).
        :return: The packed integer or the obfuscated string key.
        :raises ValueError: If a required field is missing, an unexpected field is provided,
                            or if obfuscation is requested without an Obfuskey instance.
        :raises BitOverflowError: If any value exceeds its allocated bits in the schema.
                                 (This is now primarily raised by ObfusbitSchema.validate_values).
        :raises MaximumValueError: If the packed integer exceeds the Obfuskey's maximum_value
                                   when obfuscation is enabled.
        """

        self._schema.validate_values(values)

        packed_int = 0

        for field_name, info in self._schema.field_info.items():
            value = values[field_name]
            shift = info["shift"]
            packed_int |= value << shift

        if obfuscate:
            if not self._obfuskey:
                raise ValueError(
                    "An Obfuskey instance was not provided during initialization."
                )

            return self._obfuskey.get_key(packed_int)

        return packed_int

    def unpack(
        self, packed_data: Union[int, str], obfuscated: bool = False
    ) -> Dict[str, int]:
        """
        Unpacks an integer or an obfuscated key back into a dictionary of values.

        :param packed_data: The integer or obfuscated string to unpack.
        :param obfuscated: If True, packed_data is treated as an obfuscated string
                           and de-obfuscated using the Obfuskey instance.
        :return: A dictionary where keys are field names and values are their unpacked integer values.
        :raises ValueError: If de-obfuscation is requested without an Obfuskey instance.
        :raises TypeError: If packed_data type is incorrect for the 'obfuscated' flag.
        """
        if obfuscated:
            if not self._obfuskey:
                raise ValueError(
                    "An Obfuskey instance was not provided during initialization."
                )
            if not isinstance(packed_data, str):
                raise TypeError(
                    "Input 'packed_data' must be a string when 'obfuscated' is True."
                )
            packed_int = self._obfuskey.get_value(packed_data)
        else:
            if not isinstance(packed_data, int):
                raise TypeError(
                    "Input 'packed_data' must be an integer when 'obfuscated' is False."
                )
            packed_int = packed_data

        unpacked_values = {}

        for field_name, info in self._schema.field_info.items():
            bits = info["bits"]
            shift = info["shift"]

            mask = (1 << bits) - 1
            value = (packed_int >> shift) & mask
            unpacked_values[field_name] = value

        return unpacked_values

    def pack_bytes(
        self, values: Dict[str, int], byteorder: Literal["little", "big"] = "big"
    ) -> bytes:
        """
        Packs a dictionary of values into a fixed-length bytes object.
        Internally calls `pack` and then converts the resulting integer to bytes.

        :param values: A dictionary where keys are field names and values are their integer values.
        :param byteorder: The byte order ('little' or 'big') for the output bytes.
        :return: A bytes object representing the packed values.
        :raises ValueError, BitOverflowError, MaximumValueError: Propagated from `pack`.
        """
        packed_int = self.pack(values, obfuscate=False)

        return self._int_to_bytes_internal(packed_int, byteorder)

    def unpack_bytes(
        self, byte_data: bytes, byteorder: Literal["little", "big"] = "big"
    ) -> Dict[str, int]:
        """
        Unpacks a fixed-length bytes object back into a dictionary of values.
        Internally converts the bytes to an integer and then calls `unpack`.

        :param byte_data: The bytes object to unpack.
        :param byteorder: The byte order ('little' or 'big') of the input bytes.
        :return: A dictionary where keys are field names and values are their unpacked integer values.
        :raises TypeError, ValueError: Propagated from `_bytes_to_int_internal` or `unpack`.
        """
        packed_int = self._bytes_to_int_internal(byte_data, byteorder)

        return self.unpack(packed_int, obfuscated=False)


__all__ = ("Obfusbit",)
