import asyncio

from . import common


def main():
    args = common.parse_args()
    # TODO: do I need to close loop here?
    asyncio.run(_start(args.listen_at, args.proxy_to))


async def _start(listen_at: common.Address, proxy_to: common.Address):
    server = await asyncio.start_server(
        client_connected_cb=Handler(proxy_to),
        host=listen_at.host,
        port=listen_at.port)
    async with server:
        print(f'listening at {listen_at}')
        await server.serve_forever()


class Handler:
    def __init__(self, proxy_to: common.Address):
        self._proxy_to = proxy_to

    async def __call__(self, reader, writer):
        print('got connection')
        chunk_size = 1000
        proxy_writer = None
        try:
            _, proxy_writer = await asyncio.open_connection(
                self._proxy_to.host, self._proxy_to.port)
            data = await reader.read(chunk_size)
            while data:
                print(f'read chunk with length {len(data)}')
                proxy_writer.write(data)
                await proxy_writer.drain()
                data = await reader.read(chunk_size)
        finally:
            print(f'closing connection to client')
            await _close(writer)
            if proxy_writer is not None:
                print(f'closing connection to {self._proxy_to}')
                await _close(proxy_writer)


async def _close(writer):
    writer.close()
    await writer.wait_closed()
