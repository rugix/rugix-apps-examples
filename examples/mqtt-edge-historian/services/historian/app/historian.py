import json
import os
import sqlite3
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import uvicorn
from fastapi import FastAPI


class Store:
    def __init__(self, path):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.commit()

    def insert(self, topic, payload):
        with self._lock:
            self._db.execute(
                "INSERT INTO samples (topic, payload, created_at) VALUES (?, ?, ?)",
                (topic, payload, time.time()),
            )
            self._db.commit()

    def count(self):
        with self._lock:
            row = self._db.execute("SELECT COUNT(*) FROM samples").fetchone()
        return int(row[0])

    def latest(self, limit=10):
        with self._lock:
            rows = self._db.execute(
                """
                SELECT topic, payload, created_at
                FROM samples
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        samples = []
        for topic, payload, created_at in rows:
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError:
                decoded = payload
            samples.append({"topic": topic, "payload": decoded, "created_at": created_at})
        return samples


def mqtt_client():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()
    return client


def start_mqtt(store, host, port, topic):
    client = mqtt_client()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        client.subscribe(topic, qos=1)

    def on_message(client, userdata, message):
        payload = message.payload.decode("utf-8", errors="replace")
        store.insert(message.topic, payload)

    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(host, port, keepalive=30)
            break
        except OSError:
            time.sleep(1)

    client.loop_start()
    return client


def create_app(store):
    app = FastAPI(title="Rugix Apps Edge Historian")

    @app.get("/health")
    def health():
        return {"status": "ok", "samples": store.count()}

    @app.get("/samples/latest")
    def latest(limit: int = 10):
        safe_limit = min(max(limit, 1), 100)
        samples = store.latest(safe_limit)
        return {"count": len(samples), "samples": samples}

    return app


def main():
    data_dir = Path(os.environ.get("DATA_DIR", "/data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    store = Store(data_dir / "history.sqlite")

    mqtt_host = os.environ.get("MQTT_HOST", "broker")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    mqtt_topic = os.environ.get("MQTT_TOPIC", "factory/+/+/telemetry")
    api_port = int(os.environ.get("API_PORT", "8080"))

    start_mqtt(store, mqtt_host, mqtt_port, mqtt_topic)
    app = create_app(store)
    uvicorn.run(app, host="0.0.0.0", port=api_port, log_level="info")


if __name__ == "__main__":
    main()

