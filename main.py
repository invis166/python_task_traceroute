import click
import asyncio
import socket

from src.traceroute import Traceroute, TracerouteRecord


@click.command()
@click.option('-t', '--timeout', default=200, required=False)
@click.option('-n', '--max_ttl', default=32, required=False)
@click.option('-s', '--packet_size', default=40, required=False)
@click.option('-c', '--requests_count', default=3, required=False)
@click.option('-i', '--interval', default=0, required=False)
@click.argument('dst')
def main(dst, timeout, max_ttl, packet_size, requests_count, interval):
    traceroute = Traceroute(dst, max_ttl, timeout, packet_size, requests_count, interval)
    asyncio.run(traceroute.traceroute())
    result = traceroute.get_result()

    for rec in result:
        line = [f'{rec.ttl:2}']
        if rec.ip:
            try:
                host_name = socket.gethostbyaddr(rec.ip)[0]
                line.append(host_name)
            except socket.herror:
                line.append(rec.ip)
            line.append(f'({rec.ip}) ')
        else:
            line.append('* * *')
        for t in rec.respond_time:
            line.append(f'{round(t, 2)} ms ')
        print(' '.join(line))


if __name__ == '__main__':
    main()