import json
import os
import socket
import struct
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt


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


def read_holding_registers(host, port, start, quantity, unit_id=1):
    transaction_id = int(time.time() * 1000) % 65536
    pdu = struct.pack(">BHH", 3, start, quantity)
    request = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, unit_id) + pdu
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(request)
        header = recv_exact(sock, 7)
        rx_transaction_id, protocol_id, length, _ = struct.unpack(">HHHB", header)
        if rx_transaction_id != transaction_id or protocol_id != 0:
            raise RuntimeError("invalid Modbus response header")
        response = recv_exact(sock, length - 1)
    if response[0] & 0x80:
        raise RuntimeError(f"Modbus exception {response[1]}")
    if response[0] != 3:
        raise RuntimeError(f"unexpected function code {response[0]}")
    byte_count = response[1]
    data = response[2 : 2 + byte_count]
    return [struct.unpack(">H", data[i : i + 2])[0] for i in range(0, len(data), 2)]


def mqtt_client():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()
    return client


def main():
    data_dir = Path(os.environ.get("DATA_DIR", "/data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    modbus_host = os.environ.get("MODBUS_HOST", "simulator")
    modbus_port = int(os.environ.get("MODBUS_PORT", "5020"))
    mqtt_host = os.environ.get("MQTT_HOST", "broker")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    topic = os.environ.get("MQTT_TOPIC", "factory/line-1/press-17/telemetry")
    interval = float(os.environ.get("POLL_INTERVAL_SECONDS", "2"))

    client = mqtt_client()
    while True:
        try:
            client.connect(mqtt_host, mqtt_port, keepalive=30)
            break
        except OSError:
            time.sleep(1)

    client.loop_start()
    latest = data_dir / "latest-modbus.json"

    while True:
        try:
            raw = read_holding_registers(modbus_host, modbus_port, 0, 4)
            sample = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": {
                    "protocol": "modbus-tcp",
                    "endpoint": f"{modbus_host}:{modbus_port}",
                    "asset": "press-17",
                },
                "metrics": {
                    "temperature_c": raw[0] / 10.0,
                    "pressure_kpa": raw[1],
                    "vibration_mm_s": raw[2] / 100.0,
                    "cycle_count": raw[3],
                },
            }
            payload = json.dumps(sample, separators=(",", ":"), sort_keys=True)
            client.publish(topic, payload, qos=1)
            latest.write_text(json.dumps(sample, indent=2, sort_keys=True) + "\n")
            print(payload, flush=True)
        except Exception as exc:
            print(f"poll failed: {exc}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()

