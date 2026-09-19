import json
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
SENSOR_DEFS = {
    "line-1/motor-a": {"temperature": 72, "pressure": 88, "vibration": 3.4, "humidity": 46},
    "line-1/motor-b": {"temperature": 79, "pressure": 95, "vibration": 4.2, "humidity": 52},
    "line-2/pump-1": {"temperature": 68, "pressure": 112, "vibration": 6.8, "humidity": 57},
    "line-2/compressor-1": {"temperature": 84, "pressure": 120, "vibration": 7.9, "humidity": 61},
}


def build_payload(sensor_name: str, values: dict) -> dict:
    values["temperature"] = max(40, min(120, values["temperature"] + random.uniform(-4, 7)))
    values["pressure"] = max(60, min(140, values["pressure"] + random.uniform(-6, 8)))
    values["vibration"] = max(1, min(15, values["vibration"] + random.uniform(-0.8, 1.2)))
    values["humidity"] = max(20, min(90, values["humidity"] + random.uniform(-5, 6)))
    return {
        "sensor": sensor_name,
        "temperature": round(values["temperature"], 2),
        "pressure": round(values["pressure"], 2),
        "vibration": round(values["vibration"], 2),
        "humidity": round(values["humidity"], 2),
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

print("Simulator started. Publishing industrial sensor telemetry...")

try:
    while True:
        for sensor_name, values in SENSOR_DEFS.items():
            payload = build_payload(sensor_name, values)
            topic = f"industrial/sensors/{sensor_name}"
            client.publish(topic, json.dumps(payload), qos=1)
            print(f"Published {topic}: {payload}")
        time.sleep(2)
except KeyboardInterrupt:
    print("Stopping simulator...")
finally:
    client.loop_stop()
    client.disconnect()
