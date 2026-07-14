import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from asyncua import Client


NAMESPACE_URI = "urn:rugix:examples:opcua"


def mqtt_client():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()
    return client


async def resolve_nodes(client):
    idx = await client.get_namespace_index(NAMESPACE_URI)
    machine = await client.nodes.objects.get_child([f"{idx}:CNC-7"])
    return {
        "spindle_load_pct": await machine.get_child([f"{idx}:SpindleLoadPct"]),
        "feed_rate_mm_min": await machine.get_child([f"{idx}:FeedRateMmMin"]),
        "part_count": await machine.get_child([f"{idx}:PartCount"]),
    }


async def poll_opcua(endpoint, mqtt_host, mqtt_port, topic, data_dir, interval):
    client = mqtt_client()
    while True:
        try:
            client.connect(mqtt_host, mqtt_port, keepalive=30)
            break
        except OSError:
            await asyncio.sleep(1)
    client.loop_start()

    latest = data_dir / "latest-opcua.json"

    while True:
        try:
            async with Client(url=endpoint) as opcua:
                nodes = await resolve_nodes(opcua)
                while True:
                    metrics = {}
                    for name, node in nodes.items():
                        metrics[name] = await node.read_value()
                    sample = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": {
                            "protocol": "opc-ua",
                            "endpoint": endpoint,
                            "asset": "cnc-7",
                        },
                        "metrics": metrics,
                    }
                    payload = json.dumps(sample, separators=(",", ":"), sort_keys=True)
                    client.publish(topic, payload, qos=1)
                    latest.write_text(json.dumps(sample, indent=2, sort_keys=True) + "\n")
                    print(payload, flush=True)
                    await asyncio.sleep(interval)
        except Exception as exc:
            print(f"OPC UA bridge reconnecting after error: {exc}", flush=True)
            await asyncio.sleep(2)


def main():
    data_dir = Path(os.environ.get("DATA_DIR", "/data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    endpoint = os.environ.get(
        "OPCUA_ENDPOINT", "opc.tcp://opcua-server:4840/rugix/examples/server/"
    )
    mqtt_host = os.environ.get("MQTT_HOST", "broker")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    topic = os.environ.get("MQTT_TOPIC", "factory/cell-4/cnc-7/telemetry")
    interval = float(os.environ.get("POLL_INTERVAL_SECONDS", "2"))
    asyncio.run(poll_opcua(endpoint, mqtt_host, mqtt_port, topic, data_dir, interval))


if __name__ == "__main__":
    main()

