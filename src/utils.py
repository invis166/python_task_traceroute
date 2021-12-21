import socket


def parse_ipv4_header(data: bytes, offset=0) -> tuple[int, str, str]:
    ip_header_len = (data[offset] & 0b1111) * 4
    source_ip = socket.inet_ntoa(data[offset + 12: offset + 16])
    destination_ip = socket.inet_ntoa(data[offset + 16: offset + 20])

    return ip_header_len, source_ip, destination_ip
