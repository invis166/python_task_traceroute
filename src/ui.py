import curses
from dataclasses import dataclass

from src.traceroute import Traceroute, TracerouteRecord


class TracerouteMonitoring:
    def __init__(self, traceroute: Traceroute, stdscr: curses.window):
        self._traceroute = traceroute
        self._stdscr = stdscr
        self._height, self._width = self._stdscr.getmaxyx()
        self._stat: dict[int, StatRecord] = {}

    def main(self):
        while self._stdscr.getkey() != 'q':
            res = self._get_one_traceroute()
            self._update_stat(res)
            self._draw()

    def _draw(self):
        host_block = []
        packets_block = []
        pings_block = []
        for ttl, stat in self._stat.items():
            host_block.append(str(ttl))
            host_block.append(stat.host)

            packets_block.append(str(stat.lost_percentage))
            packets_block.append(str(stat.sent_packets))

            pings_block.append(str(stat.last_resp_time))
            pings_block.append(str(stat.average_response_time))
            pings_block.append(str(stat.best_resp_time))
            pings_block.append(str(stat.worst_resp_time))



    def _update_stat(self, data: list[TracerouteRecord]):
        for traceroute_stat in data:
            ttl = traceroute_stat.ttl
            self._stat.setdefault(ttl, StatRecord(ttl=ttl, host=traceroute_stat.ip))

            self._stat[ttl].sent_packets += self._traceroute.requests_count

            responded_count = len(traceroute_stat.respond_time)
            avg_record_respond_time = round(sum(traceroute_stat.respond_time) / responded_count, 2)
            self._stat[ttl].responded_packets += responded_count
            self._stat[ttl].last_resp_time = avg_record_respond_time
            self._stat[ttl].best_resp_time = min(self._stat[ttl].best_resp_time, avg_record_respond_time)
            self._stat[ttl].worst_resp_time = max(self._stat[ttl].worst_resp_time, avg_record_respond_time)
            self._stat[ttl]._total_resp_time += sum(traceroute_stat.respond_time)

    def _get_one_traceroute(self) -> list[TracerouteRecord]:
        self._traceroute.reset()
        self._traceroute.traceroute()

        return self._traceroute.get_result()


@dataclass
class StatRecord:
    ttl: int
    host: str

    sent_packets: int = 0
    responded_packets: int = 0
    last_resp_time: float = 0
    best_resp_time: float = 0
    worst_resp_time: float = 0
    _total_resp_time: float = 0

    @property
    def lost_percentage(self):
        return round((self.responded_packets * 100) / self.sent_packets, 2)

    @property
    def average_response_time(self):
        return round(self._total_resp_time / self.responded_packets, 2)
