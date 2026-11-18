"""Local FastAPI server for Wi-Fi Sense Radar."""
from __future__ import annotations
import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

import serial
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.csi_processor import extract_features
from backend.database import EventStore
from backend.detection import PresenceDetector

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("wifi-sense-radar")
detector = PresenceDetector(int(CONFIG.get("calibration_samples", 120)), int(CONFIG.get("motion_window", 15)))
store = EventStore(str(ROOT / CONFIG.get("database_path", "data/radar.db")))
lock = threading.Lock()
latest: dict[str, Any] = {
    "connected": False, "source": "real-csi", "status": "WAITING",
    "presence": False, "calibrated": False, "packet_count": 0,
    "rssi": 0, "channel": 0, "signal_score": 0, "motion_score": 0,
    "amplitude_mean": 0, "amplitude_std": 0, "subcarriers": 0, "heat": 0,
    "message": "Waiting for receiver serial data",
}
serial_stop = threading.Event()
last_event_status = "WAITING"

def serial_worker(port: str, baud: int) -> None:
    global last_event_status
    while not serial_stop.is_set():
        try:
            log.info("Opening receiver serial port %s", port)
            with serial.Serial(port, baudrate=baud, timeout=1) as connection:
                with lock:
                    latest["message"] = "Serial connected; waiting for CSI packets"
                while not serial_stop.is_set():
                    line = connection.readline()
                    if not line:
                        continue
                    try:
                        record = json.loads(line.decode("utf-8", errors="ignore").strip())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    if record.get("type") != "csi":
                        if record.get("type") == "status":
                            with lock:
                                latest["message"] = str(record.get("state", "Receiver status"))
                        continue
                    features = extract_features(record)
                    measurement = features["amplitude_mean"] + 0.25 * features["amplitude_std"]
                    detection = detector.update(measurement)
                    with lock:
                        packet_count = int(latest.get("packet_count", 0)) + 1
                    state = {
                        **detection, "connected": True, "source": "real-csi",
                        "packet_count": packet_count, "rssi": features["rssi"],
                        "channel": features["channel"],
                        "amplitude_mean": round(features["amplitude_mean"], 2),
                        "amplitude_std": round(features["amplitude_std"], 2),
                        "subcarriers": features["subcarriers"],
                        "dropped": features["dropped"],
                        "heat": round(min(1.0, detection["signal_score"] / 100.0), 3),
                        "message": "Receiving real ESP32 CSI samples",
                        "updated_at": time.time(),
                    }
                    with lock:
                        latest.update(state)
                    if state["status"] != last_event_status and state["status"] in ("PRESENT", "EMPTY"):
                        store.add_event("presence_transition", state)
                        last_event_status = state["status"]
        except (serial.SerialException, OSError) as exc:
            log.warning("Serial connection unavailable: %s", exc)
            with lock:
                latest["connected"] = False
                latest["message"] = "Serial unavailable: " + str(exc)
            serial_stop.wait(3)

app = FastAPI(title="Wi-Fi Sense Radar", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "website")), name="static")

@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "website" / "index.html")

@app.get("/api/state")
async def api_state() -> dict[str, Any]:
    with lock:
        return dict(latest)

@app.get("/api/events")
async def api_events() -> list[dict[str, Any]]:
    return store.recent()

@app.post("/api/calibrate")
async def calibrate() -> dict[str, str]:
    detector.reset_calibration()
    with lock:
        latest.update({"calibrated": False, "presence": False, "status": "CALIBRATING",
                       "message": "Empty-area calibration started; keep the area still"})
    return {"status": "calibration_started"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            with lock:
                snapshot = dict(latest)
            await websocket.send_json(snapshot)
            await asyncio.sleep(0.15)
    except WebSocketDisconnect:
        return

@app.on_event("startup")
async def startup() -> None:
    port = CONFIG.get("serial_port")
    if port:
        threading.Thread(target=serial_worker,
                         args=(str(port), int(CONFIG.get("serial_baud", 921600))),
                         daemon=True).start()
    else:
        with lock:
            latest["message"] = "No serial_port configured. Set COM port in config.json."

@app.on_event("shutdown")
async def shutdown() -> None:
    serial_stop.set()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1",
                port=int(CONFIG.get("web_port", 8000)), reload=False)
