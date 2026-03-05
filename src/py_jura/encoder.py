"""
BLE payload encoding/decoding for JURA coffee machines.

All data sent to or received from the machine is obfuscated using a
symmetric nibble-shuffle cipher. The key is extracted from the BLE
advertisement manufacturer data (byte 0) before connecting.

Reference: Jutta-Proto/protocol-bt-cpp - ByteEncDecoder.cpp
"""

_NUMBERS1 = [14, 4, 3, 2, 1, 13, 8, 11, 6, 15, 12, 7, 10, 5, 0, 9]
_NUMBERS2 = [10, 6, 13, 12, 14, 11, 1, 9, 15, 7, 0, 5, 3, 2, 4, 8]


def _shuffle(nibble: int, cnt: int, key1: int, key2: int) -> int:
    i1 = (cnt >> 4) % 256
    i2 = _NUMBERS1[(nibble + cnt + key1) % 16]
    i3 = _NUMBERS2[(i2 + key2 + i1 - cnt - key1) % 16]
    i4 = _NUMBERS1[(i3 + key1 + cnt - key2 - i1) % 16]
    return (i4 - cnt - key1) % 16


def encdec(data: bytes | bytearray, key: int) -> bytes:
    """
    Encode or decode a JURA BLE payload.

    Applying this function twice returns the original data:
        encdec(encdec(data, key), key) == data

    Args:
        data: Payload to encode or decode.
        key:  Single byte extracted from BLE advertisement manufacturer data.

    Returns:
        Encoded or decoded bytes, same length as input.
    """
    key1 = key >> 4
    key2 = key & 0xF
    cnt = 0
    result = bytearray(len(data))

    for i, b in enumerate(data):
        high = _shuffle(b >> 4, cnt, key1, key2)
        cnt += 1
        low = _shuffle(b & 0xF, cnt, key1, key2)
        cnt += 1
        result[i] = (high << 4) | low

    return bytes(result)
