from __future__ import annotations

from typing import Dict, List, Optional, Union

from obfuskey._obfuskey import Obfuskey
from obfuskey.exceptions import BitOverflowError, MaximumValueError


class Obfusbit:
    """
    A class for efficiently packing and unpacking multiple integer values into a single
    large integer, and optionally integrating with an `Obfuskey` instance to obfuscate
    this packed integer into a fixed-length string.

    This class is ideal for scenarios where you need to combine several small pieces
    of integer data (e.g., flags, IDs, counts) into a single compact representation,
    which can then be further obfuscated for public use or simply stored compactly.
    """

    def __init__(
        self,
        schema: List[Dict[str, int]],
        *,
        obfuskey: Optional[Obfuskey] = None,
    ):
        """
        Initializes the Obfusbit packer and unpacker.

        The `schema` defines how individual integer values are combined into a single
        large integer, specifying the name and bit allocation for each value.

        :param schema: A list of dictionaries, where each dictionary defines
                       a value's name and its allocated number of bits.
                       Example: `[{"name": "user_type", "bits": 2}, {"name": "item_id", "bits": 20}]`
        :param obfuskey: An optional `Obfuskey` instance. If provided, `pack()` can
                         directly return an obfuscated string, and `unpack()` can
                         de-obfuscate an input string. If not provided, `pack()`
                         will return an integer, and `unpack()` expects an integer.
        :raises MaximumValueError: If the total bit capacity required by the schema
                                   exceeds the maximum value that the provided `Obfuskey`
                                   instance can handle.
        """
        self._schema = schema
        self._obfuskey = obfuskey
        self._total_bits = sum(item["bits"] for item in schema)
        self._max_bits = (1 << self._total_bits) - 1

        if self._obfuskey and self._max_bits > self._obfuskey.maximum_value:
            raise MaximumValueError(
                f"The provided schema requires a maximum packed integer value of {self._max_bits} "
                f"(which needs {self._total_bits} bits to represent), but the provided Obfuskey instance "
                f"can only handle up to a maximum value of {self._obfuskey.maximum_value} "
                f"(which covers {self._obfuskey.maximum_value.bit_length()} bits)."
            )

    @property
    def schema(self) -> List[Dict[str, int]]:
        """
        Returns the schema (list of dictionaries) used by this Obfusbit instance.
        """
        return self._schema

    @property
    def obfuskey(self) -> Optional[Obfuskey]:
        """
        Returns the associated Obfuskey instance, if one was provided during initialization.
        """
        return self._obfuskey

    @property
    def total_bits(self) -> int:
        """
        Returns the total number of bits required to pack all values according to the schema.
        This is the bit length of the maximum possible packed integer.
        """
        return self._total_bits

    @property
    def max_bits(self) -> int:
        """
        Returns the maximum integer value that can be represented by the schema's
        total bit allocation.
        """
        return self._max_bits

    def pack(
        self,
        values: Dict[str, int],
        *,
        obfuscate: bool = False,
    ) -> Union[str, int]:
        """
        Packs multiple integer values from a dictionary into a single large integer.
        Optionally, this packed integer can then be obfuscated into a fixed-length string
        using the associated `Obfuskey` instance.

        The order of packing is determined by the order of items in the schema,
        packing from the least significant bits (LSB) upwards.

        :param values: A dictionary where keys are the `name` from the schema
                       and values are the integers to be packed. All names defined
                       in the schema must be present in this dictionary.
        :param obfuscate: If `True`, the packed integer will be obfuscated into a string
                          using the `Obfuskey` instance provided during initialization.
                          If `False` (default), the raw packed integer is returned.
        :return: A packed integer (`int`) or an obfuscated string (`str`), depending
                 on the `obfuscate` parameter.
        :raises ValueError: If a required value for a schema item is not found in
                            the `values` dictionary, or if `obfuscate` is `True`
                            but no `Obfuskey` instance was provided.
        :raises BitOverflowError: If any integer value provided in `values` exceeds
                                  its allocated bit capacity as defined in the schema.
        :raises MaximumValueError: If the packed integer value exceeds the maximum
                                   value that the Obfuskey instance can handle (only
                                   raised if `obfuscate=True`).
        """
        packed_int = 0
        current_shift = 0

        for item in reversed(self._schema):
            value = values.get(str(item["name"]))

            if value is None:
                raise ValueError(
                    f"Required value for '{item['name']}' not provided in input values."
                )

            if not (0 <= value < (1 << item["bits"])):
                max_val_for_bits = (1 << item["bits"]) - 1
                raise BitOverflowError(
                    f"Value '{item['name']}' ({value}) exceeds its allocated {item['bits']} bits "
                    f"(maximum allowed: {max_val_for_bits})."
                )

            packed_int |= (value << current_shift)
            current_shift += item["bits"]

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
        value: Union[str, int],
        *,
        obfuscated: bool = False,
    ) -> Dict[str, int]:
        """
        Unpacks a single integer (or an obfuscated string) into multiple integer values
        according to the schema.

        The order of unpacking matches the reverse order of packing, reconstructing
        the original individual integer values.

        :param value: The packed integer (`int`) or obfuscated string (`str`) to unpack.
                      Its type should match the `obfuscated` flag.
        :param obfuscated: If `True`, `value` is treated as an obfuscated string and
                           will be de-obfuscated first using the associated `Obfuskey`
                           instance. If `False` (default), `value` is treated as a
                           raw packed integer.
        :return: A dictionary of unpacked values, where keys are the names from the
                 schema and values are the reconstructed integers.
        :raises ValueError: If `obfuscated` is `True` but no `Obfuskey` instance was
                            provided during initialization.
        :raises TypeError: If the input `value` type does not match the `obfuscated` flag
                           (e.g., `obfuscated=True` but `value` is an `int`).
        :raises UnknownKeyError: If the obfuscated key contains characters not in the Obfuskey alphabet.
        :raises KeyLengthError: If the obfuscated key's length does not match the Obfuskey instance's length.
        """
        packed_int: int

        if obfuscated:
            if not self._obfuskey:
                raise ValueError(
                    "An Obfuskey instance was not provided during initialization. "
                    "Unable to de-obfuscate the input string."
                )

            if not isinstance(value, str):
                raise TypeError(
                    f"When 'obfuscated' is True, 'value' must be a string, but received {type(value).__name__}."
                )

            packed_int = self._obfuskey.get_value(value)
        else:
            if not isinstance(value, int):
                raise TypeError(
                    f"When 'obfuscated' is False, 'value' must be an integer, but received {type(value).__name__}."
                )

            packed_int = value

        unpacked_values = {}
        current_shift = 0

        for item in reversed(self._schema):
            mask = (1 << item["bits"]) - 1
            val = (packed_int >> current_shift) & mask

            unpacked_values[str(item["name"])] = val
            current_shift += item["bits"]

        return unpacked_values
