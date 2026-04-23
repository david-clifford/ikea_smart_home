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
        
        unique_physical_devices = {}

        for d in raw_devices:
            attr = d.get("attributes", {})
            
            # 1. Try every possible battery key name found in Dirigera/Matter
            battery = (
                attr.get("batteryPercentage") or 
                attr.get("batteryLevel") or 
                attr.get("battery")
            )
            
            # 2. Use relationId if it exists, fall back to device id
            # Some Matter devices use 'id' as the primary anchor
            u_id = d.get("relationId") or d.get("id")

            if battery is not None:
                has_room = d.get("room") is not None
                
                # Update logic
                if u_id not in unique_physical_devices or has_room:
                    unique_physical_devices[u_id] = d

        print(f"--- 🔋 Deep Scan Battery Audit ---")
        print(f"{'ROOM':<15} | {'NAME':<25} | {'BATT':>4} | {'TYPE'}")
        print("-" * 80)

        for d in unique_physical_devices.values():
            attr = d.get("attributes", {})
            room_name = d.get("room", {}).get("name", "Unassigned") if d.get("room") else "Unassigned"
            name = attr.get("customName", "Unknown")
            
            # Re-fetch battery for display
            battery = attr.get("batteryPercentage") or attr.get("batteryLevel") or attr.get("battery")
            dev_type = d.get("deviceType")
            
            print(f"{room_name:<15} | {name:<25} | {battery:>3}% | {dev_type}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
