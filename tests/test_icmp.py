import pytest

from src.icmp_packet import ICMPPacket

def test_build():
    packet = ICMPPacket(
        0,
        0,
        10,
        40,
        10
    )

    assert packet.build() == b'\x00\x00\xcf\x9d\x00(\x00\n00'


def test_checksum():
    assert ICMPPacket._calculate_checksum(b'\x00\x00\x00\x00\x00(\x00\n00') == b'\xcf\x9d'
