import struct


class ICMPPacket:
    def __init__(self, packet_type: int, code: int, seq: int, identifier: int, packet_len: int):
        self.packet_type = packet_type
        self.code = code
        self.seq = seq
        self.packet_len = packet_len
        self.identifier = identifier

    def build(self) -> bytes:
        data_len = self.packet_len - (1 + 1 + 2 + 2 + 2)
        packet = struct.pack('!BBHHH',
                             self.packet_type,
                             self.code,
                             0,                 # checksum
                             self.identifier,
                             self.seq)
        packet += b'0' * data_len
        checksum = ICMPPacket._calculate_checksum(packet)

        return packet[:2] + checksum + packet[4:]

    @staticmethod
    def _calculate_checksum(packet: bytes) -> bytes:
        words = [int.from_bytes(packet[_:_ + 2], "big") for _ in range(0, len(packet), 2)]
        checksum = sum(words)
        while checksum > 0xffff:
            checksum = (checksum & 0xffff) + (checksum >> 16)

        return struct.pack('!H', 0xffff - checksum)
