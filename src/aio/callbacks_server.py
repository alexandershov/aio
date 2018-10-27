import asyncio

from . import common


def main():
    args = common.parse_args()
    asyncio.run(_start(args.listen_at, args.proxy_to))


class ClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        print(f'Client: connected to proxy {transport}')


class ProxyServerProtocol(asyncio.Protocol):
    def __init__(self, proxy_to: common.Address):
        self._proxy_to = proxy_to

    def connection_made(self, transport):
        print(f'Server: got connection {self}')
        # loop = asyncio.get_running_loop()
        # future = _connect(self._proxy_to)
        # future.add_done_callback(lambda _: print(f'connected to proxy {future.result()[1]}'))

    def data_received(self, data):
        print(f'Server: read data chunk: {data!r}')


async def _start(listen_at: common.Address, proxy_to: common.Address):
    # TODO: close sockets
    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        lambda: ProxyServerProtocol(proxy_to), listen_at.host, listen_at.port)
    async with server:
        print(f'Listening at {listen_at}')
        await server.serve_forever()


def _connect(proxy_to: common.Address):
    loop = asyncio.get_running_loop()
    coro = loop.create_connection(lambda: ClientProtocol(),
                                  proxy_to.host, proxy_to.port)
    return loop.create_task(coro)
