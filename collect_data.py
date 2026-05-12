from datetime import datetime, timezone

def collect_battery_readings(hub):
    "Return list of (timestamp, sensor, room, reading_type, value) tuples for battery levels"
    ts = datetime.now(timezone.utc).isoformat()
    raw = hub.get("/devices")
    seen = {}
    for d in raw:
        attr = d.get("attributes", {})
        battery = attr.get("batteryPercentage") or attr.get("batteryLevel")
        if battery is None: continue
        uid = d.get("relationId") or d.get("id")
        if uid not in seen or d.get("room") is not None: seen[uid] = d
    rows = []
    for d in seen.values():
        attr = d.get("attributes", {})
        name = attr.get("customName", "Unknown")
        room = d.get("room", {}).get("name", "Unassigned") if d.get("room") else "Unassigned"
        battery = attr.get("batteryPercentage") or attr.get("batteryLevel")
        rows.append((ts, name, room, "battery", battery))
    return rows

def collect_sensor_readings(hub):
    "Return list of (timestamp, sensor, room, reading_type, value) tuples for environmental sensors"
    ts = datetime.now(timezone.utc).isoformat()
    raw = hub.get("/devices")
    env_keys = dict(currentTemperature="temperature", currentRH="humidity", currentPM25="pm25", currentCO2="co2")
    merged = {}
    for d in raw:
        attr = d.get("attributes", {})
        if not any(k in attr for k in env_keys): continue
        rid = d.get("relationId") or d.get("id")
        if rid not in merged: merged[rid] = {"name": None, "room": "Unassigned", "readings": {}}
        name = attr.get("customName")
        if name and "TIMMERFLOTTE" not in name: merged[rid]["name"] = name
        if d.get("room"): merged[rid]["room"] = d["room"].get("name", "Unassigned")
        for raw_key, label in env_keys.items():
            if attr.get(raw_key) is not None: merged[rid]["readings"][label] = attr[raw_key]
    rows = []
    for s in merged.values():
        for rtype, val in s["readings"].items():
            rows.append((ts, s["name"] or "Unknown", s["room"], rtype, val))
    return rows
