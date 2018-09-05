import argparse
import asyncio
import dataclasses


def main():
    args = _parse_args()
    asyncio.run(_start_server(args.listen_at, args.proxy_to))


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen-at', required=True, type=_parse_address)
    parser.add_argument('--proxy-to', required=True, type=_parse_address)
    return parser.parse_args()


@dataclasses.dataclass
class Address:
    host: str
    port: int


class Server(asyncio.Protocol):
    def connection_made(self, transport):
        print('connected', transport)

    def data_received(self, data):
        print('data received', data)


def _parse_address(addr: str) -> Address:
    host, sep, port_str = addr.rpartition(':')
    if sep != ':':
        raise ValueError(f'`{addr}` should contain :')
    return Address(
        host=host,
        port=int(port_str))


async def _start_server(listen_at: Address, proxy_to: Address):
    loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
    server = await loop.create_server(
        protocol_factory=Server,
        host=listen_at.host,
        port=listen_at.port)
    x = 9
