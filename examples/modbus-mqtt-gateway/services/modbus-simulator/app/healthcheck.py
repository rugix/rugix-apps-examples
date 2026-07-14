import os
import socket
import struct


def recv_exact(sock, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("connection closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


host = os.environ.get("MODBUS_HOST", "127.0.0.1")
port = int(os.environ.get("MODBUS_PORT", "5020"))

with socket.create_connection((host, port), timeout=3) as sock:
    transaction_id = 1
    unit_id = 1
    pdu = struct.pack(">BHH", 3, 0, 1)
    request = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, unit_id) + pdu
    sock.sendall(request)
    header = recv_exact(sock, 7)
    _, _, length, _ = struct.unpack(">HHHB", header)
    response = recv_exact(sock, length - 1)
    if len(response) < 4 or response[0] != 3:
        raise SystemExit(1)

