import argparse
import dataclasses


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen-at', required=True, type=_parse_address)
    parser.add_argument('--proxy-to', required=True, type=_parse_address)
    return parser.parse_args()


@dataclasses.dataclass(frozen=True)
class Address:
    host: str
    port: int


def _parse_address(addr: str) -> Address:
    host, sep, port_str = addr.rpartition(':')
    if sep != ':':
        raise ValueError(f'`{addr}` should contain :')
    return Address(
        host=host,
        port=int(port_str))
