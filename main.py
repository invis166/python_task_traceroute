import click
import asyncio
import socket

from src.traceroute import Traceroute, TracerouteRecord


@click.command()
@click.option('-t', '--timeout', default=2, required=False)
@click.option('-n', '--max_ttl', default=32, required=False)
@click.option('-s', '--packet_size', default=40, required=False)
@click.option('-c', '--requests_count', default=3, required=False)
@click.option('-i', '--interval', default=0, required=False)
@click.argument('dst')
def main(dst, timeout, max_ttl, packet_size, requests_count, interval):
    traceroute = Traceroute(dst, max_ttl, timeout, packet_size, requests_count, interval)
    asyncio.run(traceroute.traceroute())
    result = traceroute.get_result()

    for rec, time in sorted(result.items(), key=lambda r, t: t):
        line = []
        if time:
            try:
                host_name = socket.gethostbyaddr(rec.ip)[0]
                line.append(host_name)
            except socket.herror:
                line.append(rec.ip)
            line.append(rec.ip)
        for t in time:
            line.append(str(t * 1000))
        print(' '.join(line))


if __name__ == '__main__':
    main()