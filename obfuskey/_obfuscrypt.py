from __future__ import annotations

import math

from typing import Dict, Optional, Tuple

from obfuskey._obfusbit import Obfusbit
from obfuskey._obfusbit_schema import ObfusbitSchema
from obfuskey._obfuskey import Obfuskey
from obfuskey.exceptions import AlgorithmError, CipherMetaError


class Obfuscrypt:
    """
    Obfuscates encryption metadata (version and algorithm) into an opaque token,
    replacing plaintext headers like ``v3:gcm:`` with an obfuscated key.

    Uses Obfusbit to pack version and algorithm ID into a single integer, then
    Obfuskey to obfuscate that integer into a fixed-length alphanumeric string.

    :param algorithms: A mapping of algorithm names to integer IDs.
                       IDs must be positive integers (0 is reserved).
    :param alphabet: The alphabet to use for the obfuscated key.
    :param version_bits: Number of bits allocated for the version field.
    :param algorithm_bits: Number of bits allocated for the algorithm field.
    :param key_length: Fixed length of the obfuscated key. If None, automatically
                       calculated from the total bits and alphabet size.
    :param multiplier: Optional odd integer multiplier for Obfuskey.
    :param separator: The separator between the obfuscated header and payload.
    """

    def __init__(
        self,
        algorithms: Dict[str, int],
        *,
        alphabet: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        version_bits: int = 4,
        algorithm_bits: int = 4,
        key_length: Optional[int] = None,
        multiplier: Optional[int] = None,
        separator: str = ":",
    ):
        self._validate_algorithms(algorithms, algorithm_bits)

        self._algorithms = dict(algorithms)
        self._algorithms_reverse: Dict[int, str] = {v: k for k, v in algorithms.items()}
        self._separator = separator
        self._version_bits = version_bits
        self._algorithm_bits = algorithm_bits

        total_bits = version_bits + algorithm_bits

        if key_length is None:
            key_length = math.ceil(total_bits / math.log2(len(alphabet)))

        self._obfuskey = Obfuskey(
            alphabet, key_length=key_length, multiplier=multiplier
        )

        schema = ObfusbitSchema(
            [
                {"name": "version", "bits": version_bits},
                {"name": "algorithm", "bits": algorithm_bits},
            ]
        )

        self._obfusbit = Obfusbit(schema, obfuskey=self._obfuskey)

    @staticmethod
    def _validate_algorithms(algorithms: Dict[str, int], algorithm_bits: int) -> None:
        """
        Validates the algorithm mapping.

        :raises ValueError: If the mapping is empty, contains non-positive IDs,
                            duplicate IDs, or IDs that exceed the bit allocation.
        """
        if not algorithms:
            raise ValueError("The algorithms mapping cannot be empty.")

        max_id = (1 << algorithm_bits) - 1
        seen_ids = set()

        for name, algo_id in algorithms.items():
            if not isinstance(name, str) or not name:
                raise ValueError(
                    f"Algorithm name must be a non-empty string, got {name!r}."
                )

            if not isinstance(algo_id, int) or algo_id <= 0:
                raise ValueError(
                    f"Algorithm ID for '{name}' must be a positive integer, got {algo_id}."
                )

            if algo_id > max_id:
                raise ValueError(
                    f"Algorithm ID for '{name}' ({algo_id}) exceeds the maximum "
                    f"allowed by {algorithm_bits} bits ({max_id})."
                )

            if algo_id in seen_ids:
                raise ValueError(
                    f"Duplicate algorithm ID {algo_id} for '{name}'."
                )

            seen_ids.add(algo_id)

    @property
    def algorithms(self) -> Dict[str, int]:
        """Returns a copy of the algorithm name-to-ID mapping."""
        return dict(self._algorithms)

    @property
    def max_version(self) -> int:
        """The maximum version number supported by the bit allocation."""
        return (1 << self._version_bits) - 1

    @property
    def max_algorithm_id(self) -> int:
        """The maximum algorithm ID supported by the bit allocation."""
        return (1 << self._algorithm_bits) - 1

    def seal(self, version: int, algorithm: str, payload: str) -> str:
        """
        Combines version, algorithm, and payload into a token with an obfuscated header.

        :param version: The encryption version number (must be > 0).
        :param algorithm: The algorithm name (must exist in the algorithms mapping).
        :param payload: The ciphertext payload (e.g., base64url-encoded nonce+ciphertext+tag).
        :return: A string in the format ``{obfuscated_header}{separator}{payload}``.
        :raises AlgorithmError: If the algorithm name is not in the mapping.
        :raises ValueError: If the version is not a positive integer.
        """
        if not isinstance(version, int) or version <= 0:
            raise ValueError(
                f"Version must be a positive integer, got {version!r}."
            )

        if algorithm not in self._algorithms:
            raise AlgorithmError(
                f"Unknown algorithm '{algorithm}'. "
                f"Known algorithms: {', '.join(sorted(self._algorithms))}."
            )

        algo_id = self._algorithms[algorithm]

        header = self._obfusbit.pack(
            {"version": version, "algorithm": algo_id},
            obfuscate=True,
        )

        return f"{header}{self._separator}{payload}"

    def unseal(self, token: str) -> Tuple[int, str, str]:
        """
        Extracts version, algorithm, and payload from an obfuscated token.

        :param token: The full token string produced by :meth:`seal`.
        :return: A tuple of ``(version, algorithm_name, payload)``.
        :raises CipherMetaError: If the token format is invalid.
        :raises AlgorithmError: If the decoded algorithm ID is not in the mapping.
        """
        parts = token.split(self._separator, 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise CipherMetaError(
                f"Invalid token format. Expected '{{header}}{self._separator}{{payload}}'."
            )

        header, payload = parts

        fields = self._obfusbit.unpack(header, obfuscated=True)
        version = fields["version"]
        algo_id = fields["algorithm"]

        if version <= 0:
            raise CipherMetaError(
                f"Decoded version must be positive, got {version}."
            )

        if algo_id not in self._algorithms_reverse:
            raise AlgorithmError(
                f"Unknown algorithm ID {algo_id}. "
                f"Known IDs: {sorted(self._algorithms_reverse)}."
            )

        algorithm = self._algorithms_reverse[algo_id]

        return version, algorithm, payload


__all__ = ("Obfuscrypt", "AlgorithmError", "CipherMetaError")
