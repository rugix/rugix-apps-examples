import json


APP_NAME = "modbus-mqtt-gateway"


def test_modbus_mqtt_gateway_publishes_plc_metrics(activate_app):
    app = activate_app(APP_NAME)

    result = app.exec("gateway", "cat", "/data/latest-modbus.json")
    sample = json.loads(result.stdout)

    assert sample["source"]["protocol"] == "modbus-tcp"
    assert sample["source"]["asset"] == "press-17"
    assert set(sample["metrics"]) >= {
        "temperature_c",
        "pressure_kpa",
        "vibration_mm_s",
        "cycle_count",
    }
    assert isinstance(sample["metrics"]["cycle_count"], int)
    assert sample["metrics"]["cycle_count"] > 0

