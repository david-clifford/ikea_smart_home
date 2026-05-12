from hub import get_hub, collect_battery_readings, collect_sensor_readings

def test_collect(hub):
    "Print all battery and sensor readings"
    for r in collect_battery_readings(hub): print(r)
    print()
    for r in collect_sensor_readings(hub): print(r)

hub = get_hub()
test_collect(hub)
