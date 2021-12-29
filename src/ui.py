import curses
import logging
import asyncio
from dataclasses import dataclass

from src.traceroute import Traceroute, TracerouteRecord


logging.basicConfig(filename='log.log', level=logging.ERROR)


class TracerouteMonitoringUI:
    def __init__(self, traceroute: Traceroute):
        self._traceroute = traceroute
        self._stdscr: curses.window = None
        self._height, self._width = 0, 0
        self._stat: dict[int, StatRecord] = {}

    def main(self, stdscr: curses.window):
        self._stdscr = stdscr
        self._stdscr.nodelay(True)
        self._height, self._width = self._stdscr.getmaxyx()

        while self._stdscr.getch() != ord('q'):
            res = self._get_one_traceroute()
            self._update_stat(res)
            self._draw()

    def _draw(self):
        self._stdscr.clear()

        lines = self._make_lines()
        logging.log(level=logging.DEBUG, msg=f'{lines}')

        offset = 0
        formatted_lines = [[] for j in range(len(lines))]
        for j in range(len(lines[0])):
            offset = len(max(lines, key=lambda line: len(line[j]))[j])
            logging.log(level=logging.DEBUG, msg=f'{offset} {j}')
            for i, line in enumerate(lines):
                if j == 1:
                    field = f'{line[j]:<{offset}}'
                else:
                    field = f'{line[j]:>{offset}}'
                formatted_lines[i].append(field)

        y_coord = 0
        for line in formatted_lines:
            self._stdscr.addstr(y_coord, 0, ' '.join(line))
            y_coord += 1

    def _make_lines(self) -> list:
        lines = []
        header = ['ttl', 'host', 'Lost', 'Sent', 'LastResp', 'AvgResp', 'BstResp', 'WrstResp']
        lines.append(header)
        for ttl, stat in self._stat.items():
            if stat.host == '':
                line = [str(ttl), 'waiting for response'] + [''] * 6
            else:
                line = [str(ttl), stat.host, str(stat.lost_percentage), str(stat.sent_packets), str(stat.last_resp_time),
                        str(stat.average_response_time), str(stat.best_resp_time), str(stat.worst_resp_time)]
            lines.append(line)

        return lines

    def _update_stat(self, data: list[TracerouteRecord]):
        for traceroute_stat in data:
            if len(traceroute_stat.respond_time) > self._traceroute.requests_count:
                logging.log(level=logging.ERROR, msg=f'{traceroute_stat}')
            ttl = traceroute_stat.ttl
            self._stat.setdefault(ttl, StatRecord(ttl=ttl, host=traceroute_stat.ip))

            self._stat[ttl].sent_packets += self._traceroute.requests_count

            responded_count = len(traceroute_stat.respond_time)
            if responded_count == 0:
                avg_record_respond_time = 0
            else:
                avg_record_respond_time = round(sum(traceroute_stat.respond_time) / responded_count, 2)
            self._stat[ttl].responded_packets += responded_count
            self._stat[ttl].last_resp_time = avg_record_respond_time
            self._stat[ttl].best_resp_time = min(self._stat[ttl].best_resp_time, avg_record_respond_time)
            self._stat[ttl].worst_resp_time = max(self._stat[ttl].worst_resp_time, avg_record_respond_time)
            self._stat[ttl]._total_resp_time += sum(traceroute_stat.respond_time)

    def _get_one_traceroute(self) -> list[TracerouteRecord]:
        self._traceroute.reset()
        logging.log(level=logging.DEBUG, msg='reset')
        asyncio.run(self._traceroute.traceroute())

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
        if self.sent_packets == 0:
            return 0
        return round(100 - (self.responded_packets * 100) / self.sent_packets, 2)

    @property
    def average_response_time(self):
        if self.responded_packets == 0:
            return 0
        return round(self._total_resp_time / self.responded_packets, 2)
