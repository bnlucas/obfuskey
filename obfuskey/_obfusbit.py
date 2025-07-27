from __future__ import annotations

from typing import Dict, Literal, List, Optional, Union

from obfuskey._obfusbit_schema import ObfusbitSchema
from obfuskey._obfuskey import Obfuskey
from obfuskey.exceptions import (
    MaximumValueError,
    BitOverflowError,
)


class Obfusbit:
    """
    Obfusbit is a utility for packing and unpacking multiple integer values
    into a single large integer or a fixed-length byte sequence, based on a defined schema.
    It can optionally use an `Obfuskey` instance to obfuscate the packed integer
    into an alphanumeric string representation.

    :param schema: The schema definition. This can be a list of dictionaries,
                   where each dictionary defines a field with 'name' (str) and 'bits' (int),
                   or an already-instantiated `ObfusbitSchema` object.
    :param obfuskey: An optional `Obfuskey` instance to enable obfuscation/de-obfuscation.
                     Defaults to `None`.
    :raises MaximumValueError: If the schema's total bit capacity exceeds the
                               `obfuskey` instance's maximum value, when an `obfuskey`
                               is provided.
    :raises SchemaValidationError: If the provided `schema` (when it's a list) is invalid.
    """

    def __init__(
        self,
        schema: Union[List[Dict[str, int]], ObfusbitSchema],
        *,
        obfuskey: Optional[Obfuskey] = None,
    ):
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

    @property
    def total_bits(self) -> int:
        """
        The total number of bits defined by the schema.

        :return: The total number of bits.
        :rtype: int
        """
        return self._schema.total_bits

    @property
    def max_bits(self) -> int:
        """
        The maximum possible integer value that can be packed according to the schema.
        This is (2^total_bits) - 1.

        :return: The maximum integer value.
        :rtype: int
        """
        return self._schema.max_bits

    @property
    def schema(self) -> List[Dict[str, int]]:
        """
        The raw schema definition list used by this Obfusbit instance.

        :return: A list of dictionaries representing the schema.
        :rtype: List[Dict[str, int]]
        """
        return self._schema.definition

    @property
    def obfuskey(self) -> Optional[Obfuskey]:
        """
        The Obfuskey instance associated with this Obfusbit instance, if any.

        :return: An Obfuskey instance or None.
        :rtype: Optional[Obfuskey]
        """
        return self._obfuskey

    def _get_required_byte_length(self) -> int:
        """
        Calculates the minimum number of bytes required to store the packed integer
        based on the schema's total bits.

        :return: The required byte length.
        :rtype: int
        """
        return (self._schema.total_bits + 7) // 8

    def _int_to_bytes_internal(
        self,
        packed_int: int,
        byteorder: Literal["little", "big"],
    ) -> bytes:
        """
        Converts a packed integer into a fixed-length byte sequence.

        :param packed_int: The integer value to convert.
        :param byteorder: The byte order ('little' or 'big') for conversion.
        :return: A bytes object representing the integer.
        :raises ValueError: If the packed_int is out of range for the schema's capacity.
        :rtype: bytes
        """
        byte_length = self._get_required_byte_length()

        if not (0 <= packed_int <= self._schema.max_bits):
            raise ValueError(
                f"Packed integer {packed_int} is out of range (0 to {self._schema.max_bits}) "
                f"for the schema's total bit capacity."
            )

        return packed_int.to_bytes(byte_length, byteorder=byteorder)

    def _bytes_to_int_internal(
        self,
        byte_data: bytes,
        byteorder: Literal["little", "big"],
    ) -> int:
        """
        Converts a byte sequence back into an integer.

        :param byte_data: The bytes object to convert.
        :param byteorder: The byte order ('little' or 'big') used during conversion.
        :return: The converted integer value.
        :raises TypeError: If `byte_data` is not a bytes object.
        :raises ValueError: If the length of `byte_data` does not match the
                            expected length for the schema.
        :rtype: int
        """
        expected_byte_length = self._get_required_byte_length()
        if not isinstance(byte_data, bytes):
            raise TypeError("Input 'byte_data' must be a bytes object.")

        if len(byte_data) != expected_byte_length:
            raise ValueError(
                f"Byte data length ({len(byte_data)}) does not match expected length "
                f"for this schema ({expected_byte_length} bytes based on {self._schema.total_bits} bits)."
            )

        return int.from_bytes(byte_data, byteorder=byteorder)

    def pack(
        self,
        values: Dict[str, int],
        *,
        obfuscate: bool = False,
    ) -> Union[str, int]:
        """
        Packs multiple integer values from a dictionary into a single large integer.
        Optionally obfuscates the packed integer into an alphanumeric string if an
        `Obfuskey` instance is provided during initialization.

        The order of packing is determined by the schema definition, with earlier
        fields in the schema occupying lower bit positions in the resulting integer.

        :param values: A dictionary where keys are field names (str) from the schema
                       and values are the integers to be packed. All names defined
                       in the schema must be present.
        :param obfuscate: If `True`, the packed integer will be obfuscated using
                          the `Obfuskey` instance. Defaults to `False`.
        :return: The packed integer (int) or an obfuscated string (str) if `obfuscate` is `True`.
        :raises ValueError: If a required field is missing from `values`, or if
                            `obfuscate` is True but no `Obfuskey` was provided.
        :raises BitOverflowError: If any value in `values` exceeds its allocated bits
                                  as defined in the schema.
        :raises MaximumValueError: If the packed integer value exceeds the maximum
                                   capacity of the associated `Obfuskey` instance (only checked if obfuscating).
        :rtype: Union[str, int]
        """
        packed_int = 0

        for item in self._schema.definition:
            item_name = str(item["name"])
            info = self._schema.get_field_info(item_name)

            value = values.get(item_name)

            if value is None:
                raise ValueError(
                    f"Required value for '{item_name}' not provided in input values."
                )

            bits = info["bits"]
            shift = info["shift"]

            if not (0 <= value < (1 << bits)):
                max_val_for_bits = (1 << bits) - 1
                raise BitOverflowError(
                    f"Value '{item_name}' ({value}) exceeds its allocated {bits} bits "
                    f"(maximum allowed: {max_val_for_bits})."
                )

            packed_int |= value << shift

        if obfuscate:
            if not self._obfuskey:
                raise ValueError(
                    "An Obfuskey instance was not provided during initialization. "
                    "Unable to obfuscate the packed integer."
                )

            if packed_int > self._obfuskey.maximum_value:
                raise MaximumValueError(
                    f"The packed integer value ({packed_int}) generated from the schema "
                    f"exceeds the maximum value allowed by the associated Obfuskey instance "
                    f"({self._obfuskey.maximum_value}). Adjust schema bit allocation or Obfuskey's key_length."
                )
            return self._obfuskey.get_key(packed_int)

        return packed_int

    def unpack(
        self,
        packed_data: Union[str, int],
        *,
        obfuscated: bool = False,
    ) -> Dict[str, int]:
        """
        Unpacks a packed integer (or an obfuscated string) back into a dictionary
        of original integer values based on the schema.

        :param packed_data: The integer or obfuscated string to unpack.
        :param obfuscated: If `True`, `packed_data` is treated as an obfuscated string
                           and will be de-obfuscated first. Defaults to `False`.
        :return: A dictionary where keys are field names (str) and values are the
                 unpacked integer values.
        :raises TypeError: If input types are incorrect (e.g., string for non-obfuscated data).
        :raises ValueError: If `obfuscated` is `True` but no `Obfuskey` was provided.
        :raises KeyLengthError: If an obfuscated key has an incorrect length.
        :raises UnknownKeyError: If an obfuscated key contains invalid characters.
        :rtype: Dict[str, int]
        """
        if obfuscated:
            if not self._obfuskey:
                raise ValueError(
                    "An Obfuskey instance was not provided during initialization. "
                    "Unable to de-obfuscate the packed integer."
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

        for item in self._schema.definition:
            name = str(item["name"])
            info = self._schema.get_field_info(name)
            bits = info["bits"]
            shift = info["shift"]

            mask = (1 << bits) - 1
            value = (packed_int >> shift) & mask
            unpacked_values[name] = value

        return unpacked_values

    def pack_bytes(
        self,
        values: Dict[str, int],
        byteorder: Literal["little", "big"] = "big",
    ) -> bytes:
        """
        Packs multiple integer values into a fixed-length byte sequence.
        This method first packs the values into a single large integer, then converts
        that integer into bytes. It does not perform obfuscation.

        :param values: A dictionary where keys are field names (str) from the schema
                       and values are the integers to be packed.
        :param byteorder: The byte order ('big' or 'little'). Defaults to 'big'.
        :return: A bytes object representing the packed data.
        :raises ValueError: If a required value is missing, or `packed_int` is out of range.
        :raises BitOverflowError: If any value exceeds its allocated bits.
        :rtype: bytes
        """
        packed_int = self.pack(values, obfuscate=False)
        return self._int_to_bytes_internal(packed_int, byteorder)

    def unpack_bytes(
        self,
        byte_data: bytes,
        byteorder: Literal["little", "big"] = "big",
    ) -> Dict[str, int]:
        """
        Unpacks a fixed-length byte sequence back into a dictionary of integer values.
        This method first converts the byte sequence into a single large integer,
        then unpacks that integer into the original values. It does not perform
        de-obfuscation.

        :param byte_data: The bytes object to unpack. Its length must match
                          the schema's required byte length.
        :param byteorder: The byte order ('big' or 'little'). Defaults to 'big'.
        :return: A dictionary of unpacked integer values.
        :raises TypeError: If `byte_data` is not a bytes object.
        :raises ValueError: If the length of `byte_data` does not match the expected length.
        :rtype: Dict[str, int]
        """
        packed_int = self._bytes_to_int_internal(byte_data, byteorder)
        return self.unpack(packed_int, obfuscated=False)


__all__ = ("Obfusbit",)
