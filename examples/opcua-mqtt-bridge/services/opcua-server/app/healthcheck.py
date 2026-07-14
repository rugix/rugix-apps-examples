import os
import socket
from urllib.parse import urlparse

endpoint = os.environ.get(
    "OPCUA_ENDPOINT", "opc.tcp://127.0.0.1:4840/rugix/examples/server/"
)
parsed = urlparse(endpoint)
host = parsed.hostname or "127.0.0.1"
port = parsed.port or 4840

with socket.create_connection((host, port), timeout=3):
    pass

