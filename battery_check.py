from dotenv import load_dotenv
from hub import get_hub

load_dotenv()

def main():

    try:
        hub = get_hub()
        raw_devices = hub.get("/devices")
        
        unique_physical_devices = {}

        # 1. Deduplicate by relationId (primary) or id (fallback)
        for d in raw_devices:
            attr = d.get("attributes", {})
            battery = attr.get("batteryPercentage") or attr.get("batteryLevel")
            u_id = d.get("relationId") or d.get("id")

            if battery is not None:
                has_room = d.get("room") is not None
                if u_id not in unique_physical_devices or has_room:
                    unique_physical_devices[u_id] = d

        # 2. Group by Type
        grouped = {}
        for d in unique_physical_devices.values():
            dtype = d.get("deviceType", "Other")
            if dtype not in grouped:
                grouped[dtype] = []
            grouped[dtype].append(d)

        print(f"--- Categorized Battery Report ---")
        header = f"{'ROOM':<13} | {'NAME':<10} | {'BATT':>4} | {'STATUS'}"
        dashedLine = "-" * len(header)
        print(dashedLine)
        print(header)
        print(dashedLine)

        # 3. Output by Group
        for dtype, devices in sorted(grouped.items()):
            # Format the header nicely (e.g., contactSensor -> CONTACTSENSOR)
            print(f"\n[{dtype.upper()}]")
            print(dashedLine)
            
            # Sort devices by room name within the category
            for d in sorted(devices, key=lambda x: x.get("room", {}).get("name", "Unassigned")):
                attr = d.get("attributes", {})
                room_name = d.get("room", {}).get("name", "Unassigned") if d.get("room") else "Unassigned"
                name = attr.get("customName", "Unknown")
                battery = attr.get("batteryPercentage") or attr.get("batteryLevel")
                
                status = "OK"
                if battery < 20: status = "LOW!"
                if battery < 10: status = "CRITICAL"
                
                print(f"{room_name:<13} | {name:<10} | {battery:>3}% | {status}")

            print(dashedLine)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
