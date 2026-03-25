from __future__ import annotations

import pytest

from obfuskey import Obfuscrypt, alphabets
from obfuskey.exceptions import AlgorithmError, CipherMetaError


ALGORITHMS = {
    "gcm": 1,
    "cbc": 2,
    "chacha20": 3,
    "xts": 4,
}


class TestObfuscrypt:
    """Tests for the Obfuscrypt class."""

    @pytest.fixture
    def crypt(self):
        return Obfuscrypt(ALGORITHMS)

    @pytest.fixture
    def crypt_custom(self):
        return Obfuscrypt(
            ALGORITHMS,
            alphabet=alphabets.BASE36,
            version_bits=3,
            algorithm_bits=3,
            key_length=3,
            separator=".",
        )

    def test_init_default(self, crypt):
        """Test default initialization."""
        assert crypt.algorithms == ALGORITHMS
        assert crypt.max_version == 15
        assert crypt.max_algorithm_id == 15

    def test_init_custom_bits(self):
        """Test initialization with custom bit allocations."""
        crypt = Obfuscrypt({"aes": 1}, version_bits=8, algorithm_bits=8)
        assert crypt.max_version == 255
        assert crypt.max_algorithm_id == 255

    def test_init_empty_algorithms_raises(self):
        """Test that empty algorithms mapping raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Obfuscrypt({})

    def test_init_zero_algorithm_id_raises(self):
        """Test that algorithm ID of 0 raises ValueError."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            Obfuscrypt({"gcm": 0})

    def test_init_negative_algorithm_id_raises(self):
        """Test that negative algorithm ID raises ValueError."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            Obfuscrypt({"gcm": -1})

    def test_init_algorithm_id_exceeds_bits_raises(self):
        """Test that algorithm ID exceeding bit capacity raises ValueError."""
        with pytest.raises(ValueError, match="exceeds the maximum"):
            Obfuscrypt({"gcm": 16}, algorithm_bits=4)

    def test_init_duplicate_algorithm_id_raises(self):
        """Test that duplicate algorithm IDs raise ValueError."""
        with pytest.raises(ValueError, match="Duplicate algorithm ID"):
            Obfuscrypt({"gcm": 1, "cbc": 1})

    def test_init_empty_algorithm_name_raises(self):
        """Test that empty algorithm name raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            Obfuscrypt({"": 1})

    def test_seal_and_unseal_roundtrip(self, crypt):
        """Test that seal/unseal roundtrips correctly."""
        payload = "8B2xkP7nQr5m3Z"

        for version in [1, 2, 3, 10, 15]:
            for algo in ALGORITHMS:
                token = crypt.seal(version, algo, payload)
                v, a, p = crypt.unseal(token)
                assert v == version
                assert a == algo
                assert p == payload

    def test_seal_produces_opaque_header(self, crypt):
        """Test that the header does not contain plaintext version/algorithm."""
        token = crypt.seal(3, "gcm", "payload123")
        header = token.split(":")[0]

        assert "gcm" not in header
        assert "3" not in header or len(header) > 1

    def test_seal_different_versions_produce_different_headers(self, crypt):
        """Test that different versions produce different obfuscated headers."""
        t1 = crypt.seal(1, "gcm", "payload")
        t2 = crypt.seal(2, "gcm", "payload")
        h1 = t1.split(":")[0]
        h2 = t2.split(":")[0]

        assert h1 != h2

    def test_seal_different_algorithms_produce_different_headers(self, crypt):
        """Test that different algorithms produce different obfuscated headers."""
        t1 = crypt.seal(1, "gcm", "payload")
        t2 = crypt.seal(1, "cbc", "payload")
        h1 = t1.split(":")[0]
        h2 = t2.split(":")[0]

        assert h1 != h2

    def test_seal_unknown_algorithm_raises(self, crypt):
        """Test that sealing with an unknown algorithm raises AlgorithmError."""
        with pytest.raises(AlgorithmError, match="Unknown algorithm 'unknown'"):
            crypt.seal(1, "unknown", "payload")

    def test_seal_zero_version_raises(self, crypt):
        """Test that version 0 raises ValueError."""
        with pytest.raises(ValueError, match="positive integer"):
            crypt.seal(0, "gcm", "payload")

    def test_seal_negative_version_raises(self, crypt):
        """Test that negative version raises ValueError."""
        with pytest.raises(ValueError, match="positive integer"):
            crypt.seal(-1, "gcm", "payload")

    def test_unseal_invalid_format_no_separator(self, crypt):
        """Test that a token without separator raises CipherMetaError."""
        with pytest.raises(CipherMetaError, match="Invalid token format"):
            crypt.unseal("noseparatorhere")

    def test_unseal_invalid_format_empty_parts(self, crypt):
        """Test that a token with empty header or payload raises CipherMetaError."""
        with pytest.raises(CipherMetaError, match="Invalid token format"):
            crypt.unseal(":payload")

        with pytest.raises(CipherMetaError, match="Invalid token format"):
            crypt.unseal("header:")

    def test_custom_separator(self, crypt_custom):
        """Test seal/unseal with a custom separator."""
        token = crypt_custom.seal(1, "gcm", "payload")
        assert "." in token
        assert ":" not in token

        v, a, p = crypt_custom.unseal(token)
        assert v == 1
        assert a == "gcm"
        assert p == "payload"

    def test_custom_alphabet(self, crypt_custom):
        """Test that custom alphabet produces valid tokens."""
        token = crypt_custom.seal(2, "cbc", "data")
        header = token.split(".")[0]

        for ch in header:
            assert ch in alphabets.BASE36

    def test_payload_with_separator(self, crypt):
        """Test that payload containing the separator character is preserved."""
        payload = "nonce:ciphertext:tag"
        token = crypt.seal(1, "gcm", payload)
        v, a, p = crypt.unseal(token)

        assert p == payload

    def test_with_explicit_multiplier(self):
        """Test initialization with an explicit multiplier."""
        crypt = Obfuscrypt({"gcm": 1}, multiplier=12345)
        token = crypt.seal(1, "gcm", "payload")
        v, a, p = crypt.unseal(token)

        assert v == 1
        assert a == "gcm"
        assert p == "payload"

    def test_algorithms_property_returns_copy(self, crypt):
        """Test that algorithms property returns a copy."""
        algos = crypt.algorithms
        algos["new"] = 99
        assert "new" not in crypt.algorithms

    def test_realistic_encryption_roundtrip(self):
        """
        Test a realistic encryption-as-service scenario where the plaintext
        format v{version}:{algorithm}:{payload} is replaced with an opaque header.
        """
        algorithms = {
            "aes-128-gcm": 1,
            "aes-256-gcm": 2,
            "chacha20-poly1305": 3,
        }

        crypt = Obfuscrypt(
            algorithms,
            alphabet=alphabets.BASE62,
            version_bits=4,
            algorithm_bits=4,
        )

        # Simulate: original would be "v1:aes-256-gcm:9xPqR..."
        payload = "9xPqR7mNkL2bVwYz"
        token = crypt.seal(1, "aes-256-gcm", payload)

        # The token should NOT contain plaintext metadata
        assert "aes-256-gcm" not in token
        assert token.startswith("v1:") is False

        # But we can recover everything
        version, algorithm, recovered_payload = crypt.unseal(token)
        assert version == 1
        assert algorithm == "aes-256-gcm"
        assert recovered_payload == payload
