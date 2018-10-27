import asyncio
import collections

from . import common


def main():
    args = common.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_start(args.listen_at, args.proxy_to, loop))


class ClientProtocol(asyncio.Protocol):
    def __init__(self, callbacks):
        self._server_protocol = callbacks

    def connection_made(self, transport):
        print(f'Client: connection_made, transport: {transport}')
        self._server_protocol.connected_to_proxy(transport)


class ProxyServerProtocol(asyncio.Protocol):
    def __init__(self, proxy_to: common.Address, event):
        self._proxy_to = proxy_to
        self._event = event
        self._proxy_transport = None
        self._buffer = collections.deque()
        self._transport = None

    def connection_made(self, transport):
        print('Server: connection_made')
        self._transport = transport
        _connect(self._proxy_to, self)

    def data_received(self, data):
        print(f'Server: data_received {data!r}')
        self._buffer.append(data)
        if self._proxy_transport is not None:
            self._flush()

    def connection_lost(self, exc):
        print('Server: connection_lost')
        if self._proxy_transport is not None:
            print('Server: closing proxy_transport')
            self._proxy_transport.close()
        print('Server setting event')
        self._event.set()

    def connected_to_proxy(self, transport):
        self._proxy_transport = transport
        self._flush()

    def _flush(self):
        assert self._proxy_transport is not None
        print(f'Server: flushing {len(self._buffer)} chunks')
        while self._buffer:
            chunk = self._buffer.popleft()
            self._proxy_transport.write(chunk)
        if self._transport.is_closing():
            print('Server: closing proxy_transport')
            self._proxy_transport.close()


def _start(listen_at: common.Address, proxy_to: common.Address, loop):
    print(f'Loop is running: {loop.is_running()}')
    event = asyncio.Event()
    coro = loop.create_server(
        lambda: ProxyServerProtocol(proxy_to, event), listen_at.host, listen_at.port)
    loop.create_task(coro)
    print(f'Listening at {listen_at}')
    return event.wait()


def _connect(proxy_to: common.Address, server_protocol):
    loop = asyncio.get_running_loop()
    coro = loop.create_connection(lambda: ClientProtocol(server_protocol),
                                  proxy_to.host, proxy_to.port)
    return loop.create_task(coro)
