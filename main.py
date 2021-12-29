import click
import curses

from src.traceroute import Traceroute, TracerouteRecord
from src.ui import TracerouteMonitoringUI


@click.command()
@click.option('-t', '--timeout', default=200, required=False)
@click.option('-n', '--max_ttl', default=32, required=False)
@click.option('-s', '--packet_size', default=40, required=False)
@click.option('-c', '--requests_count', default=3, required=False)
@click.option('-i', '--interval', default=0, required=False)
@click.argument('dst')
def main(dst, timeout, max_ttl, packet_size, requests_count, interval):
    traceroute = Traceroute(
        dest=dst,
        max_ttl=max_ttl,
        timeout=timeout,
        packet_size=packet_size,
        requests_count=requests_count,
        interval=interval
    )
    app = TracerouteMonitoringUI(traceroute)
    curses.wrapper(app.main)


if __name__ == '__main__':
    main()
