import asyncio
import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, List

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

APP_ROOT = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(APP_ROOT, "static")

app = FastAPI(title="Industrial Sensor Monitor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state
sensor_state: Dict[str, Dict[str, Any]] = {}
alert_state: List[Dict[str, Any]] = []
recent_readings: List[Dict[str, Any]] = []
readings_lock = threading.Lock()

mqtt_client = None
mqtt_connected = False


class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        for connection in list(self.connections):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


def normalize_sensor(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    timestamp = payload.get("timestamp") or datetime.utcnow().isoformat(timespec="seconds") + "Z"
    sensor = {
        "name": name,
        "temperature": float(payload.get("temperature", 0)),
        "pressure": float(payload.get("pressure", 0)),
        "vibration": float(payload.get("vibration", 0)),
        "humidity": float(payload.get("humidity", 0)),
        "status": payload.get("status", "normal"),
        "timestamp": timestamp,
    }
    sensor["status"] = determine_status(sensor)
    return sensor


def determine_status(sensor: Dict[str, Any]) -> str:
    if sensor["temperature"] > 80 or sensor["pressure"] > 110 or sensor["vibration"] > 8 or sensor["humidity"] > 75:
        return "warning"
    if sensor["temperature"] > 100 or sensor["pressure"] > 130 or sensor["vibration"] > 12 or sensor["humidity"] > 90:
        return "critical"
    return "normal"


def evaluate_alert(sensor: Dict[str, Any]) -> Dict[str, Any] | None:
    if sensor["status"] == "normal":
        return None
    return {
        "sensor": sensor["name"],
        "level": sensor["status"],
        "message": f"{sensor['name']} exceeds safe operating thresholds",
        "timestamp": sensor["timestamp"],
    }


def snapshot_state() -> Dict[str, Any]:
    with readings_lock:
        sensors = list(sensor_state.values())
        alerts = list(alert_state)
        history = list(recent_readings)
    return {
        "sensors": sensors,
        "alerts": alerts,
        "history": history,
        "mqtt_connected": mqtt_connected,
    }


async def push_update():
    payload = snapshot_state()
    await manager.broadcast({"type": "update", "data": payload})


def persist_reading(sensor: Dict[str, Any]):
    with readings_lock:
        sensor_state[sensor["name"]] = sensor
        recent_readings.insert(0, sensor)
        recent_readings[:] = recent_readings[:20]

        alert = evaluate_alert(sensor)
        if alert:
            alert_state.insert(0, alert)
            alert_state[:] = alert_state[:10]
        else:
            existing = [a for a in alert_state if a["sensor"] == sensor["name"]]
            if existing:
                alert_state[:] = [a for a in alert_state if a["sensor"] != sensor["name"]]


async def handle_sensor_message(topic: str, payload: Dict[str, Any]):
    sensor_name = topic.split("/")[-1]
    sensor = normalize_sensor(sensor_name, payload)
    persist_reading(sensor)
    await push_update()


def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        return

    try:
        asyncio.run(handle_sensor_message(msg.topic, data))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_sensor_message(msg.topic, data))
        loop.close()


def connect_mqtt():
    global mqtt_client, mqtt_connected
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.subscribe("industrial/sensors/#", qos=1)
        mqtt_client.loop_start()
        mqtt_connected = True
    except Exception as exc:
        mqtt_connected = False
        print(f"MQTT broker unavailable: {exc}")


def on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    global mqtt_connected
    mqtt_connected = True
    client.subscribe("industrial/sensors/#", qos=1)
    print("Connected to MQTT broker")


# Fallback demo generator
async def generate_demo_data():
    demo_sensors = {
        "motor-a": {"temperature": 72, "pressure": 88, "vibration": 3.4, "humidity": 46},
        "motor-b": {"temperature": 79, "pressure": 95, "vibration": 4.2, "humidity": 52},
        "pump-1": {"temperature": 68, "pressure": 112, "vibration": 6.8, "humidity": 57},
        "compressor-1": {"temperature": 84, "pressure": 120, "vibration": 7.9, "humidity": 61},
    }
    while True:
        await asyncio.sleep(2)
        if mqtt_connected:
            continue
        for name, values in demo_sensors.items():
            values["temperature"] += (hash(name) % 9) - 4
            values["pressure"] += (hash(name + "p") % 11) - 5
            values["vibration"] += (hash(name + "v") % 5) * 0.2 - 0.4
            values["humidity"] += (hash(name + "h") % 7) - 3
            payload = {
                "temperature": max(40, min(120, values["temperature"])),
                "pressure": max(60, min(140, values["pressure"])),
                "vibration": max(1, min(15, values["vibration"])),
                "humidity": max(20, min(90, values["humidity"])),
                "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
            await handle_sensor_message(f"industrial/sensors/line-1/{name}", payload)


@app.on_event("startup")
async def startup_event():
    connect_mqtt()
    asyncio.create_task(generate_demo_data())


@app.get("/api/health")
async def health():
    return {"status": "ok", "mqtt_connected": mqtt_connected, "sensors": len(sensor_state)}


@app.post("/api/sensor")
async def ingest_sensor(data: Dict[str, Any]):
    topic = data.get("topic", "industrial/sensors/demo")
    payload = data.get("payload", {})
    await handle_sensor_message(topic, payload)
    return {"status": "accepted"}


@app.get("/api/snapshot")
async def snapshot():
    return snapshot_state()


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_text(json.dumps({"type": "update", "data": snapshot_state()}))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
