"""Tests for the JURA BLE payload encoder/decoder."""

import pytest

from py_jura.encoder import encdec


def test_known_vector():
    """Ground truth from C++ test suite: encdec([0x18], 0x2A) == [0x42]."""
    assert encdec(bytes([0x18]), 0x2A) == bytes([0x42])


def test_symmetric_single_byte():
    assert encdec(encdec(bytes([0x18]), 0x2A), 0x2A) == bytes([0x18])


def test_symmetric_multi_byte():
    data = bytes(range(16))
    assert encdec(encdec(data, 0x2A), 0x2A) == data


@pytest.mark.parametrize("key", [0x00, 0x0F, 0x2A, 0xF0, 0xFF])
def test_symmetric_across_keys(key):
    data = bytes(range(256))
    assert encdec(encdec(data, key), key) == data


def test_empty():
    assert encdec(b"", 0x2A) == b""


def test_accepts_bytearray():
    result = encdec(bytearray([0x18]), 0x2A)
    assert result == bytes([0x42])


def test_returns_bytes():
    assert isinstance(encdec(b"\x00", 0x2A), bytes)


def test_same_length():
    data = bytes(range(32))
    assert len(encdec(data, 0x2A)) == len(data)
