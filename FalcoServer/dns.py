from socket import socket, AF_INET, SOCK_DGRAM
from struct import pack, unpack
from uasyncio import sleep_ms

def parse_qname_end(packet, offset):
    while True:
        length = packet[offset]
        offset += 1
        if length == 0:
            break
        offset += length
    return offset


def build_dns_response(query, ip_bytes):
    txid = query[0:2]
    flags = unpack(">H", query[2:4])[0]
    rd = flags & 0x0100
    resp_flags = 0x8000 | 0x0400 | rd
    header = (
        txid +
        pack(">H", resp_flags) +
        pack(">H", 1) +
        pack(">H", 1) +
        b"\x00\x00\x00\x00"
    )
    qname_end = parse_qname_end(query, 12)
    question = query[12:qname_end + 4]
    answer = (
        b"\xC0\x0C" +
        b"\x00\x01" +
        b"\x00\x01" +
        pack(">I", 30) +
        b"\x00\x04" +
        ip_bytes
    )
    return header + question + answer

async def dns_server(local_ip):
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind(("0.0.0.0", 53))
    ip_bytes = bytes(map(int, local_ip.split(".")))
    while True:
        try:
            data, addr = sock.recvfrom(512)
        except OSError:
            await sleep_ms(0)
            continue
        if len(data) < 12:
            continue
        try:
            resp = build_dns_response(data, ip_bytes)
            sock.sendto(resp, addr)
        except Exception:
            pass
