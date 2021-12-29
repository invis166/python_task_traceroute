import random
import asyncio
import socket
import time
from dataclasses import dataclass, field

from src.utils import *
from src.icmp_packet import ICMPPacket


ECHO_RESPONSE = 0
TTL_RESPONSE = 11


class Traceroute:
    def __init__(self, dest, max_ttl=30, timeout=200, packet_size=40, requests_count=3, interval=0):
        self.dest = socket.gethostbyname(dest)
        self.max_ttl = max_ttl
        self.timeout = timeout
        self.packet_size = packet_size
        self.requests_count = requests_count
        self.interval = interval

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self._socket.setblocking(False)
        self._identifier = random.randint(0, 255)
        self._curr_seq = 0
        self._pending_requests: dict[int, float] = {}
        self._is_reached_dst = False
        self._responded: dict[int, TracerouteRecord] = {}

    async def traceroute(self):
        await asyncio.gather(self._start_sender(), self._start_receiver())

    def get_result(self) -> list["TracerouteRecord"]:
        res = []
        for ttl in range(1, self.max_ttl):
            rec = self._responded[ttl]
            res.append(rec)
            if rec.ip == self.dest:
                break

        return res

    def reset(self):
        self._identifier = random.randint(0, 255)
        self._curr_seq = 0
        self._pending_requests = {}
        self._is_reached_dst = False
        self._responded = {}

    async def _start_sender(self):
        curr_ttl = 1
        while curr_ttl <= self.max_ttl and not self._is_reached_dst:
            self._responded.setdefault(curr_ttl, TracerouteRecord(ip='', ttl=curr_ttl))
            self._socket.setsockopt(socket.SOL_IP, socket.IP_TTL, curr_ttl)
            for j in range(self.requests_count):
                self._send_echo()
                await asyncio.sleep(self.interval)
            curr_ttl += 1

        self._is_reached_dst = True

    async def _start_receiver(self):
        loop = asyncio.get_event_loop()
        while not self._is_reached_dst or self._pending_requests:
            self._clear_timed_out_requests()
            try:
                resp = await asyncio.wait_for(loop.sock_recv(self._socket, 65536), timeout=1)
            except asyncio.TimeoutError:
                continue
            self._handle_response(resp)

    def _send_echo(self):
        packet = self._get_ping_icmp_packet()
        self._socket.sendto(packet, (self.dest, 0))
        self._pending_requests[self._curr_seq] = time.perf_counter() * 1000
        self._curr_seq = (self._curr_seq + 1) % 256

    def _handle_response(self, resp: bytes):
        ip_header_len, source_ip, _ = parse_ipv4_header(resp)
        message_type = resp[ip_header_len]
        if message_type == TTL_RESPONSE or message_type == ECHO_RESPONSE:
            if message_type == TTL_RESPONSE:
                icmp_header_len = 8
                offset_to_nested_ip = ip_header_len + icmp_header_len
                nested_ip_header_len, _, nested_ip_dest = parse_ipv4_header(resp, offset_to_nested_ip)

                if nested_ip_dest != self.dest:
                    return

                offset_to_nested_icmp = ip_header_len + icmp_header_len + nested_ip_header_len
                identifier = get_identifier_from_icmp(resp, offset_to_nested_icmp)
                seq = get_seq_from_icmp(resp, offset_to_nested_icmp)
            else:
                identifier = get_identifier_from_icmp(resp, ip_header_len)
                seq = get_seq_from_icmp(resp, ip_header_len)

            if identifier != self._identifier:
                return
            if seq not in self._pending_requests:
                return
            if source_ip == self.dest:
                self._is_reached_dst = True

            respond_time = (time.perf_counter() * 1000 - self._pending_requests[seq])
            if respond_time > self.timeout:
                del self._pending_requests[seq]
                return

            ttl = seq // self.requests_count + 1
            self._responded[ttl].ip = source_ip
            self._responded[ttl].respond_time.append(respond_time)

    def _get_ping_icmp_packet(self) -> bytes:
        packet = ICMPPacket(8, 0, self._curr_seq, self._identifier, self.packet_size)

        return packet.build()

    def _clear_timed_out_requests(self):
        now = time.perf_counter() * 1000
        self._pending_requests = {req: t
                                  for req, t in self._pending_requests.items()
                                  if (now - t) < self.timeout}


@dataclass
class TracerouteRecord:
    ip: str
    ttl: int
    respond_time: list[float] = field(default_factory=lambda: [])  # плохое название
