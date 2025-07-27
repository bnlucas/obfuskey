from __future__ import annotations

import pytest

from obfuskey import Obfusbit, ObfusbitSchema, Obfuskey, alphabets
from obfuskey.exceptions import (
    BitOverflowError,
    MaximumValueError,
    SchemaValidationError,
)


class TestObfusbit:
    """
    Pytest tests for the Obfusbit class.
    """

    SIMPLE_SCHEMA_DEF = [
        {"name": "id", "bits": 10},  # Max value 1023
        {"name": "type", "bits": 2},  # Max value 3
        {"name": "flag", "bits": 1},  # Max value 1
    ]

    @pytest.fixture
    def simple_schema(self):
        return ObfusbitSchema(self.SIMPLE_SCHEMA_DEF)

    @pytest.fixture
    def obfuskey_instance(self):
        return Obfuskey(alphabets.BASE62, key_length=3)

    @pytest.fixture
    def obfuskey_too_small(self):
        return Obfuskey(alphabets.BASE62, key_length=1)

    def test_init_with_list_schema(self, simple_schema):
        """
        Test initialization with a list of dictionaries for schema.
        """
        obfusbit = Obfusbit(self.SIMPLE_SCHEMA_DEF)
        assert isinstance(obfusbit._schema, ObfusbitSchema)
        assert obfusbit.total_bits == 13
        assert obfusbit.max_bits == 8191
        assert obfusbit.obfuskey is None

    def test_init_with_obfusbitschema_object(self, simple_schema):
        """
        Test initialization with an existing ObfusbitSchema object.
        """
        obfusbit = Obfusbit(simple_schema)
        assert obfusbit._schema is simple_schema
        assert obfusbit.total_bits == 13
        assert obfusbit.max_bits == 8191

    def test_init_with_obfuskey(self, simple_schema, obfuskey_instance):
        """
        Test initialization with an Obfuskey instance.
        """
        obfusbit = Obfusbit(simple_schema, obfuskey=obfuskey_instance)
        assert obfusbit.obfuskey is obfuskey_instance

    def test_init_raises_maximumvalueerror_if_obfuskey_too_small(
        self, simple_schema, obfuskey_too_small
    ):
        """
        Test that initialization raises MaximumValueError if Obfuskey cannot handle schema's max value.
        """
        with pytest.raises(
            MaximumValueError,
            match="The provided schema requires a maximum packed integer value of 8191",
        ):
            Obfusbit(simple_schema, obfuskey=obfuskey_too_small)

    def test_init_raises_schema_validation_error(self):
        """
        Test that initialization propagates SchemaValidationError from ObfusbitSchema.
        """
        invalid_schema_def = [{"name": "f1", "bits": 0}]  # Invalid bits
        with pytest.raises(
            SchemaValidationError, match="'bits' must be a positive integer"
        ):
            Obfusbit(invalid_schema_def)

    def test_properties_return_correct_values(self, simple_schema, obfuskey_instance):
        """
        Test that properties (total_bits, max_bits, schema, obfuskey) return correct values.
        """
        obfusbit = Obfusbit(simple_schema, obfuskey=obfuskey_instance)
        assert obfusbit.total_bits == 13
        assert obfusbit.max_bits == 8191
        assert obfusbit.schema == self.SIMPLE_SCHEMA_DEF
        assert obfusbit.obfuskey is obfuskey_instance

    @pytest.mark.parametrize(
        "total_bits, packed_int, byteorder, expected_bytes, expected_byte_length",
        [
            (8, 255, "big", b"\xff", 1),  # 8 bits, max value
            (8, 0, "big", b"\x00", 1),  # 8 bits, min value
            (
                12,
                1234,
                "big",
                b"\x04\xd2",
                2,
            ),  # 12 bits, needs 2 bytes. (1234 = 0b010011010010)
            (12, 1234, "little", b"\xd2\x04", 2),
            (16, 65535, "big", b"\xff\xff", 2),  # 16 bits, max value
            (1, 1, "big", b"\x01", 1),  # 1 bit, needs 1 byte
            (1, 0, "big", b"\x00", 1),  # 1 bit, needs 1 byte
            (7, 127, "big", b"\x7f", 1),  # 7 bits, needs 1 byte
            (
                9,
                511,
                "big",
                b"\x01\xff",
                2,
            ),  # 9 bits, needs 2 bytes (511 = 0b111111111)
        ],
    )
    def test_int_to_bytes_internal(
        self,
        total_bits,
        packed_int,
        byteorder,
        expected_bytes,
        expected_byte_length,
        monkeypatch,
    ):
        """
        Test the _int_to_bytes_internal method.
        Requires mocking _schema for total_bits and max_bits.
        """
        mock_schema = ObfusbitSchema([{"name": "mock", "bits": total_bits}])

        obfusbit = Obfusbit(mock_schema)

        # Explicitly set _total_bits and _max_bits for the test case as Obfusbit.__init__
        # already computed them from mock_schema.
        # This part is largely for clarity, as the mock_schema already sets them.
        obfusbit._total_bits = total_bits
        obfusbit._max_bits = (1 << total_bits) - 1

        assert obfusbit._int_to_bytes_internal(packed_int, byteorder) == expected_bytes
        assert obfusbit._get_required_byte_length() == expected_byte_length

    @pytest.mark.parametrize(
        "total_bits, packed_int, byteorder, error_message_part",
        [
            (
                8,
                256,
                "big",
                r"Packed integer 256 is out of range \(0 to 255\) for the schema's total bit capacity\.",
            ),  # Too high
            (
                8,
                -1,
                "big",
                r"Packed integer -1 is out of range \(0 to 255\) for the schema's total bit capacity\.",
            ),  # Too low
        ],
    )
    def test_int_to_bytes_internal_raises_value_error(
        self, total_bits, packed_int, byteorder, error_message_part, monkeypatch
    ):
        """
        Test _int_to_bytes_internal raises ValueError for out-of-range packed_int.
        """
        mock_schema = ObfusbitSchema([{"name": "mock", "bits": total_bits}])
        obfusbit = Obfusbit(mock_schema)
        obfusbit._total_bits = total_bits
        obfusbit._max_bits = (1 << total_bits) - 1

        with pytest.raises(ValueError, match=error_message_part):
            obfusbit._int_to_bytes_internal(packed_int, byteorder)

    @pytest.mark.parametrize(
        "total_bits, byte_data, byteorder, expected_int, expected_byte_length",
        [
            (8, b"\xff", "big", 255, 1),
            (8, b"\x00", "big", 0, 1),
            (12, b"\x04\xd2", "big", 1234, 2),
            (12, b"\xd2\x04", "little", 1234, 2),
            (16, b"\xff\xff", "big", 65535, 2),
        ],
    )
    def test_bytes_to_int_internal(
        self,
        total_bits,
        byte_data,
        byteorder,
        expected_int,
        expected_byte_length,
        monkeypatch,
    ):
        """
        Test _bytes_to_int_internal for correct conversion.
        Requires mocking _schema for total_bits.
        """
        mock_schema = ObfusbitSchema([{"name": "mock", "bits": total_bits}])
        obfusbit = Obfusbit(mock_schema)
        obfusbit._total_bits = (
            total_bits  # ensure the _total_bits property reflects the mock
        )

        assert obfusbit._bytes_to_int_internal(byte_data, byteorder) == expected_int
        assert obfusbit._get_required_byte_length() == expected_byte_length

    @pytest.mark.parametrize(
        "total_bits, byte_data, byteorder, error_type, error_message_part",
        [
            (
                8,
                "not_bytes",
                "big",
                TypeError,
                "Input 'byte_data' must be a bytes object.",
            ),
            (
                8,
                b"\xff\x00",
                "big",
                ValueError,
                r"Byte data length \(2\) does not match expected length for this schema \(1 bytes based on 8 bits\)\.",
            ),
            (
                16,
                b"\xff",
                "big",
                ValueError,
                r"Byte data length \(1\) does not match expected length for this schema \(2 bytes based on 16 bits\)\.",
            ),
        ],
    )
    def test_bytes_to_int_internal_raises_error(
        self,
        total_bits,
        byte_data,
        byteorder,
        error_type,
        error_message_part,
        monkeypatch,
    ):
        """
        Test _bytes_to_int_internal raises TypeError or ValueError for invalid inputs.
        """
        mock_schema = ObfusbitSchema([{"name": "mock", "bits": total_bits}])
        obfusbit = Obfusbit(mock_schema)
        obfusbit._total_bits = total_bits

        with pytest.raises(error_type, match=error_message_part):
            obfusbit._bytes_to_int_internal(byte_data, byteorder)

    def test_pack_success_no_obfuscation(self, simple_schema):
        """
        Test successful packing without obfuscation.
        Schema: id (10 bits, shift 3), type (2 bits, shift 1), flag (1 bit, shift 0)
        Packed order: ID_ID_ID_ID_ID_ID_ID_ID_ID_ID | TYPE_TYPE | FLAG
        """
        # flag=1 (0b1) << 0 = 0b1
        # type=2 (0b10) << 1 = 0b100 (because flag is 1 bit, type starts at shift 1)
        # id=100 (0b1100100) << 3 = 0b1100100000 (because type (2) + flag (1) = 3 bits shifted)
        # Packed: 0b1100100000000 | 0b100 | 0b1 (this order is if the shift starts from LSB based on definition order)
        # No, it's shift 0 for the LAST element in schema, which is 'flag'.
        # So 'flag' is LSB.
        # 'id': 100 (0b1100100) -> Shifted by 3 (flag:1 + type:2 = 3) -> 0b1100100_000
        # 'type': 2 (0b10) -> Shifted by 1 (flag:1) -> 0b10_0
        # 'flag': 1 (0b1) -> Shifted by 0 -> 0b1

        # Packed = (id << 3) | (type << 1) | (flag << 0)
        # (100 << 3) = 100 * 8 = 800 (0b1100100000)
        # (2 << 1) = 4 (0b100)
        # (1 << 0) = 1 (0b1)
        # 800 | 4 | 1 = 805
        # 0b11001000000 | 0b100 | 0b1
        # = 0b11001001001
        # Correct calculations from `_calculate_field_info`:
        # 'flag': {'bits': 1, 'shift': 0}
        # 'type': {'bits': 2, 'shift': 1}
        # 'id':   {'bits': 10, 'shift': 3}
        # packed_int = (values["id"] << 3) | (values["type"] << 1) | (values["flag"] << 0)
        # packed_int = (100 << 3) | (2 << 1) | (1 << 0)
        # packed_int = (100 * 8) | (2 * 2) | (1 * 1)
        # packed_int = 800 | 4 | 1
        # packed_int = 805

        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 2, "flag": 1}
        expected_packed_int = 805

        assert obfusbit.pack(values) == expected_packed_int

    def test_pack_success_with_obfuscation(self, simple_schema, obfuskey_instance):
        """
        Test successful packing with obfuscation.
        """
        obfusbit = Obfusbit(simple_schema, obfuskey=obfuskey_instance)
        values = {"id": 100, "type": 2, "flag": 1}
        packed_int = 805
        expected_obfuscated_key = obfuskey_instance.get_key(packed_int)

        assert obfusbit.pack(values, obfuscate=True) == expected_obfuscated_key

    def test_pack_raises_valueerror_missing_field(self, simple_schema):
        """
        Test pack raises ValueError when a required field is missing.
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 2}

        with pytest.raises(
            ValueError,
            match="Required values for the following fields are missing: flag.",
        ):
            obfusbit.pack(values)

    def test_pack_raises_valueerror_extra_field(self, simple_schema):
        """
        Test pack raises ValueError when an extra field is provided.
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 2, "flag": 1, "extra_field": 5}

        with pytest.raises(
            ValueError, match="Unexpected fields provided in input values: extra_field"
        ):
            obfusbit.pack(values)

    def test_pack_raises_bitoverflowerror(self, simple_schema):
        """
        Test pack raises BitOverflowError when a value exceeds its allocated bits.
        'type' has 2 bits, max value is 3 (0b11)
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 4, "flag": 1}  # type=4 needs 3 bits

        with pytest.raises(
            BitOverflowError,
            match="Value 'type' \\(4\\) exceeds its allocated 2 bits \\(maximum allowed: 3\\).",
        ):
            obfusbit.pack(values)

    def test_pack_raises_valueerror_no_obfuskey_for_obfuscation(self, simple_schema):
        """
        Test pack raises ValueError if obfuscate=True but no Obfuskey was provided.
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 2, "flag": 1}

        with pytest.raises(
            ValueError,
            match="An Obfuskey instance was not provided during initialization.",
        ):
            obfusbit.pack(values, obfuscate=True)

    def test_pack_raises_maximumvalueerror_obfuscated_value_too_large(self):
        """
        Test pack raises MaximumValueError if packed_int exceeds Obfuskey's max_value.
        Create a schema that results in a large packed_int, and an Obfuskey that's too small.
        NOTE: With current design, this error is often caught during Obfusbit initialization
        if Obfuskey's maximum_value is less than schema's total_bits capacity.
        This test as written confirms the Obfusbit.__init__ error.
        """
        schema_def = [
            {"name": "a", "bits": 10},
            {"name": "b", "bits": 2},
            {"name": "c", "bits": 1},
        ]
        obfuskey_small = Obfuskey(alphabets.BASE62, key_length=1)

        with pytest.raises(
            MaximumValueError,
            match=r"integer value of 8191 \(which needs 13 bits to represent\)",
        ):
            Obfusbit(schema_def, obfuskey=obfuskey_small)

    def test_unpack_success_no_obfuscation(self, simple_schema):
        """
        Test successful unpacking from an integer.
        """
        obfusbit = Obfusbit(simple_schema)
        packed_int = 805
        expected_values = {"id": 100, "type": 2, "flag": 1}

        assert obfusbit.unpack(packed_int) == expected_values

    def test_unpack_success_with_obfuscation(self, simple_schema, obfuskey_instance):
        """
        Test successful unpacking from an obfuscated string.
        """
        obfusbit = Obfusbit(simple_schema, obfuskey=obfuskey_instance)
        packed_int = 805
        obfuscated_key = obfuskey_instance.get_key(packed_int)
        expected_values = {"id": 100, "type": 2, "flag": 1}

        assert obfusbit.unpack(obfuscated_key, obfuscated=True) == expected_values

    def test_unpack_raises_valueerror_no_obfuskey_for_deobfuscation(
        self, simple_schema
    ):
        """
        Test unpack raises ValueError if obfuscated=True but no Obfuskey.
        """
        obfusbit = Obfusbit(simple_schema)

        with pytest.raises(
            ValueError,
            match="An Obfuskey instance was not provided during initialization.",
        ):
            obfusbit.unpack("some_key", obfuscated=True)

    def test_unpack_raises_typeerror_for_incorrect_packed_data_type(
        self, simple_schema, obfuskey_instance
    ):
        """
        Test unpack raises TypeError for incorrect packed_data type.
        """
        obfusbit = Obfusbit(simple_schema)
        with pytest.raises(
            TypeError,
            match="Input 'packed_data' must be an integer when 'obfuscated' is False.",
        ):
            obfusbit.unpack("not_an_int", obfuscated=False)

        obfusbit_with_key = Obfusbit(simple_schema, obfuskey=obfuskey_instance)
        with pytest.raises(
            TypeError,
            match="Input 'packed_data' must be a string when 'obfuscated' is True.",
        ):
            obfusbit_with_key.unpack(12345, obfuscated=True)

    def test_pack_bytes_success(self, simple_schema):
        """
        Test successful packing to bytes.
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 2, "flag": 1}

        # Packed int is 805 (0b11001001001)
        # Total bits = 13. Required bytes = (13 + 7) // 8 = 2 bytes.
        # 805 in 2 bytes big-endian: 0x0325 (0b00000011 00100101)
        # 805 in 2 bytes little-endian: 0x2503 (0b00100101 00000011)
        # The result from pack() is 805
        # 805.to_bytes(2, 'big') = b'\x03\x25'
        # 805.to_bytes(2, 'little') = b'\x25\x03'

        assert obfusbit.pack_bytes(values, byteorder="big") == b"\x03\x25"
        assert obfusbit.pack_bytes(values, byteorder="little") == b"\x25\x03"

    def test_pack_bytes_raises_bitoverflowerror(self, simple_schema):
        """
        Test pack_bytes raises BitOverflowError, as it uses pack internally.
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 4, "flag": 1}

        with pytest.raises(BitOverflowError):
            obfusbit.pack_bytes(values)

    def test_pack_bytes_raises_valueerror_missing_field(self, simple_schema):
        """
        Test pack_bytes raises ValueError for a missing field, as it uses pack internally.
        """
        obfusbit = Obfusbit(simple_schema)
        values = {"id": 100, "type": 2}

        with pytest.raises(
            ValueError,
            match="Required values for the following fields are missing: flag.",
        ):
            obfusbit.pack_bytes(values)

    def test_unpack_bytes_success(self, simple_schema):
        """
        Test successful unpacking from bytes.
        """
        obfusbit = Obfusbit(simple_schema)
        byte_data_big = b"\x03\x25"
        byte_data_little = b"\x25\x03"
        expected_values = {"id": 100, "type": 2, "flag": 1}

        assert obfusbit.unpack_bytes(byte_data_big, byteorder="big") == expected_values
        assert (
            obfusbit.unpack_bytes(byte_data_little, byteorder="little")
            == expected_values
        )

    def test_unpack_bytes_raises_typeerror_invalid_input_type(self, simple_schema):
        """
        Test unpack_bytes raises TypeError for non-bytes input.
        """
        obfusbit = Obfusbit(simple_schema)

        with pytest.raises(
            TypeError, match="Input 'byte_data' must be a bytes object."
        ):
            obfusbit.unpack_bytes("not_bytes_data")

    def test_unpack_bytes_raises_valueerror_incorrect_length(self, simple_schema):
        """
        Test unpack_bytes raises ValueError for byte data with incorrect length.
        Schema needs 2 bytes.
        """
        obfusbit = Obfusbit(simple_schema)

        with pytest.raises(
            ValueError,
            match=r"Byte data length \(1\) does not match expected length for this schema",
        ):
            obfusbit.unpack_bytes(b"\x01")

        with pytest.raises(
            ValueError,
            match=r"Byte data length \(3\) does not match expected length for this schema",
        ):
            obfusbit.unpack_bytes(b"\x01\x02\x03")
