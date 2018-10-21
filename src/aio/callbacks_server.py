import asyncio

from . import common


def main():
    args = common.parse_args()
    asyncio.run(_start(args.listen_at, args.proxy_to))


class ClientProtocol(asyncio.Protocol):
    def __init__(self, server):
        self._server = server

    def connection_made(self, transport):
        print('Connected to client')
        self._server.client_transport = transport


class ProxyServerProtocol(asyncio.Protocol):
    def __init__(self, proxy_to: common.Address):
        self._proxy_to = proxy_to
        self.client_transport = None
        self._chunks = []

    def connection_made(self, transport):
        print('Got connection')
        loop = asyncio.get_running_loop()
        _connect(self, self._proxy_to)

    def data_received(self, data):
        if self.client_transport is not None:
            self._flush_chunks()
            self.client_transport.write(data)
            print(f'Read chunk with length {len(data)}')
        else:
            self._chunks.append(data)

    def _flush_chunks(self):
        while self._chunks:
            self.client_transport.write(self._chunks.pop())


async def _start(listen_at: common.Address, proxy_to: common.Address):
    loop = asyncio.get_running_loop()
    server_protocol = ProxyServerProtocol(proxy_to)
    try:
        server = await loop.create_server(
            lambda: server_protocol, listen_at.host, listen_at.port)
        async with server:
            print(f'Listening at {listen_at}')
            await server.serve_forever()
    finally:
        if server_protocol.client_transport is not None:
            server_protocol.client_transport.close()


def _connect(server_protocol, proxy_to: common.Address):
    loop = asyncio.get_running_loop()
    coro = loop.create_connection(lambda: ClientProtocol(server_protocol),
                                  proxy_to.host, proxy_to.port)
    loop.create_task(coro)
