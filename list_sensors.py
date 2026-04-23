import os
from dotenv import load_dotenv
from dirigera import Hub

load_dotenv()
token = os.getenv("DIRIGERA_TOKEN")
hub_ip = os.getenv("DIRIGERA_IP")

def main():
    if not hub_ip or not token:
        print("Error: DIRIGERA_IP or DIRIGERA_TOKEN not found.")
        return

    try:
        hub = Hub(token=token, ip_address=hub_ip)
        raw_devices = hub.get("/devices")
        
        merged_sensors = {}

        for d in raw_devices:
            attr = d.get("attributes", {})
            # Look for any environmental keys
            has_env_data = any(k in attr for k in ["currentTemperature", "currentRH", "currentPM25", "currentCO2"])
            
            if has_env_data:
                rel_id = d.get("relationId") or d.get("id")
                
                if rel_id not in merged_sensors:
                    merged_sensors[rel_id] = {
                        "name": attr.get("customName"),
                        "temp": None,
                        "hum": None,
                        "pm25": None,
                        "co2": None
                    }
                
                # Prioritize custom names (TH1, AQk) over generic model names
                current_name = attr.get("customName")
                if current_name and "TIMMERFLOTTE" not in current_name:
                    merged_sensors[rel_id]["name"] = current_name

                # Mapping raw API keys to our merged dictionary
                if attr.get("currentTemperature") is not None:
                    merged_sensors[rel_id]["temp"] = attr.get("currentTemperature")
                if attr.get("currentRH") is not None:
                    merged_sensors[rel_id]["hum"] = attr.get("currentRH")
                if attr.get("currentPM25") is not None:
                    merged_sensors[rel_id]["pm25"] = attr.get("currentPM25")
                if attr.get("currentCO2") is not None:
                    merged_sensors[rel_id]["co2"] = attr.get("currentCO2")

        # Table Header
        header = f"{'DEVICE NAME':<11} | {'TEMP':<8} | {'RH':<4} | {'PM2.5':<5} | {'CO2':<4} |"
        dashedLine = "-" * len(header)
        print(dashedLine)
        print(header)
        print(dashedLine)

        # Print sorted by name (TH1, TH2, etc.)
        for sensor in sorted(merged_sensors.values(), key=lambda x: x["name"] or "Unknown"):
            name = sensor["name"] or "Unknown Device"
            temp = f"{sensor['temp']:.1f}°C" if sensor['temp'] is not None else "--"
            hum  = f"{sensor['hum']}%" if sensor['hum'] is not None else "--"
            pm25 = str(sensor['pm25']) if sensor['pm25'] is not None else "--"
            co2  = str(sensor['co2']) if sensor['co2'] is not None else "--"

            print(f"{name:<11} | {temp:<8} | {hum:<4} | {pm25:<5} | {co2:<4} |")

        print(dashedLine)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
