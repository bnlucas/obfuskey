from __future__ import annotations

BASE16: str = "0123456789ABCDEF"
BASE32: str = "234567ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE36: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE52: str = "0123456789BCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz"
BASE56: str = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
BASE58: str = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE62: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE64: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/"
BASE94: str = (
    "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
)

CROCKFORD_BASE32: str = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ZBASE32: str = "ybndrfg8ejkmcpqxot1uwisza345h769"

BASE64_URL_SAFE: str = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
)

__all__ = (
    BASE16,
    BASE32,
    BASE36,
    BASE52,
    BASE56,
    BASE58,
    BASE62,
    BASE64,
    BASE94,
    CROCKFORD_BASE32,
    ZBASE32,
    BASE64_URL_SAFE,
)
