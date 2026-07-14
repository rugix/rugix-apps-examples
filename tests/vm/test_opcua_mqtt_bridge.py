import json


APP_NAME = "opcua-mqtt-bridge"


def test_opcua_mqtt_bridge_publishes_machine_metrics(activate_app):
    app = activate_app(APP_NAME)

    result = app.exec("bridge", "cat", "/data/latest-opcua.json")
    sample = json.loads(result.stdout)

    assert sample["source"]["protocol"] == "opc-ua"
    assert sample["source"]["asset"] == "cnc-7"
    assert set(sample["metrics"]) >= {
        "spindle_load_pct",
        "feed_rate_mm_min",
        "part_count",
    }
    assert sample["metrics"]["part_count"] > 0

