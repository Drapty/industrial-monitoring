# Industrial Sensor Monitoring Platform

This project implements a universal industrial sensor monitoring application using the architecture:

Simulator -> Eclipse Mosquitto -> FastAPI -> HTML/JS dashboard

## Features

- MQTT-capable ingestion from simulator
- FastAPI backend for telemetry storage and in-memory alerts
- Real-time dashboard with WebSocket updates
- Live sensor cards, alarm panel, and recent history table
- HTTP fallback mode when no MQTT broker is available locally

## Run locally

1. Open a terminal in the project root.
2. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Start the full stack:
   ```powershell
   python run_all.py
   ```
5. Open the dashboard in the browser:
   ```text
   http://localhost:8000/
   ```

## MQTT broker

For a real Mosquitto setup on Windows, install the broker and start it locally:

```powershell
winget install --id Mosquitto.Mosquitto --accept-source-agreements --accept-package-agreements
mosquitto -v
```

Then the simulator will automatically publish to `industrial/sensors/#`.

## Topics

- `industrial/sensors/line-1/motor-a`
- `industrial/sensors/line-1/motor-b`
- `industrial/sensors/line-2/pump-1`
- `industrial/sensors/line-2/compressor-1`


