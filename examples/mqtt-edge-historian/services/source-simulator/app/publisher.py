import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt


def mqtt_client():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()
    return client


def main():
    mqtt_host = os.environ.get("MQTT_HOST", "broker")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    topic = os.environ.get("MQTT_TOPIC", "factory/line-2/welder-3/telemetry")
    interval = float(os.environ.get("PUBLISH_INTERVAL_SECONDS", "1"))

    client = mqtt_client()
    while True:
        try:
            client.connect(mqtt_host, mqtt_port, keepalive=30)
            break
        except OSError:
            time.sleep(1)

    client.loop_start()
    Path("/tmp/publisher-ready").write_text("ready\n")
    count = 0

    while True:
        now = time.time()
        count += 1
        sample = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": {
                "protocol": "mqtt",
                "asset": "welder-3",
                "cell": "line-2",
            },
            "metrics": {
                "current_a": round(112 + 16 * math.sin(now / 7), 2),
                "voltage_v": round(24 + 1.5 * math.sin(now / 11), 2),
                "duty_cycle_pct": round(61 + 9 * math.sin(now / 13), 2),
                "sample_count": count,
            },
        }
        client.publish(topic, json.dumps(sample, separators=(",", ":"), sort_keys=True), qos=1)
        time.sleep(interval)


if __name__ == "__main__":
    main()

