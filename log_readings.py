from hub import get_hub, init_db, save_readings, collect_sensor_readings, collect_battery_readings
import sys

hub = get_hub()
con = init_db()

mode = sys.argv[1] if len(sys.argv) > 1 else "sensors"
if mode == "battery": save_readings(con, collect_battery_readings(hub))
else:                  save_readings(con, collect_sensor_readings(hub))
con.close()
