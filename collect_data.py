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
