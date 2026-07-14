import math
import os
import socketserver
import struct
import threading
import time


class RegisterBank:
    def __init__(self):
        self._lock = threading.Lock()
        self._registers = [0] * 32

    def update_forever(self):
        cycle = 0
        while True:
            now = time.time()
            temperature_c10 = int(420 + 35 * math.sin(now / 13))
            pressure_kpa = int(240 + 18 * math.sin(now / 9))
            vibration_mm_s100 = int(110 + 20 * math.sin(now / 5))
            cycle += 1
            with self._lock:
                self._registers[0] = temperature_c10
                self._registers[1] = pressure_kpa
                self._registers[2] = vibration_mm_s100
                self._registers[3] = cycle % 65536
            time.sleep(1)

    def read(self, start, quantity):
        with self._lock:
            values = self._registers[start : start + quantity]
        if len(values) != quantity:
            raise ValueError("register range outside simulator bank")
        return values


registers = RegisterBank()


def recv_exact(sock, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            return b""
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class ModbusHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            header = recv_exact(self.request, 7)
            if not header:
                return
            transaction_id, protocol_id, length, unit_id = struct.unpack(">HHHB", header)
            if protocol_id != 0 or length < 2:
                return
            pdu = recv_exact(self.request, length - 1)
            if not pdu:
                return

            function = pdu[0]
            if function == 3 and len(pdu) >= 5:
                start, quantity = struct.unpack(">HH", pdu[1:5])
                try:
                    values = registers.read(start, quantity)
                    body = b"".join(struct.pack(">H", value & 0xFFFF) for value in values)
                    response_pdu = bytes([function, len(body)]) + body
                except ValueError:
                    response_pdu = bytes([function | 0x80, 2])
            else:
                response_pdu = bytes([function | 0x80, 1])

            response = struct.pack(
                ">HHHB", transaction_id, 0, len(response_pdu) + 1, unit_id
            ) + response_pdu
            self.request.sendall(response)


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    port = int(os.environ.get("MODBUS_PORT", "5020"))
    threading.Thread(target=registers.update_forever, daemon=True).start()
    with ThreadedServer(("0.0.0.0", port), ModbusHandler) as server:
        print(f"Modbus simulator listening on {port}", flush=True)
        server.serve_forever()

