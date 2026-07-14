import json


APP_NAME = "mqtt-edge-historian"


def test_mqtt_edge_historian_records_samples(activate_app):
    app = activate_app(APP_NAME)

    result = app.exec("historian", "python", "/app/check_history.py")
    sample = json.loads(result.stdout)

    assert sample["topic"] == "factory/line-2/welder-3/telemetry"
    payload = sample["payload"]
    assert payload["source"]["asset"] == "welder-3"
    assert set(payload["metrics"]) >= {
        "current_a",
        "voltage_v",
        "duty_cycle_pct",
        "sample_count",
    }
    assert payload["metrics"]["sample_count"] > 0

