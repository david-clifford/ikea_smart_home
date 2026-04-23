import os
from dotenv import load_dotenv
from dirigera import Hub

# Load credentials
load_dotenv()
token = os.getenv("DIRIGERA_TOKEN")
hub_ip = os.getenv("DIRIGERA_IP") # Your specific variable

def get_battery_status(devices, category_name):
    if not devices:
        return
        
    print(f"\n--- {category_name} ---")
    found_any_battery = False
    
    for d in devices:
        # Newer Matter devices (MYGGBETT/MYGGSPRAY) report battery in attributes
        battery = getattr(d.attributes, "battery_percentage", None)
        
        if battery is not None:
            found_any_battery = True
            name = d.attributes.custom_name
            room = d.room.name if hasattr(d, "room") and d.room else "Unassigned"
            
            status = "OK"
            if battery < 20:
                status = "LOW!"
            elif battery < 10:
                status = "CRITICAL"
                
            print(f"{room:<13} | {name:<30} | {battery:>3}% | {status}")
    
    if not found_any_battery:
        print(f"No battery data found for {category_name} (check if devices are offline).")

def main():
    if not hub_ip or not token:
        print("Error: DIRIGERA_IP or DIRIGERA_TOKEN not found in .env file.")
        return

    try:
        hub = Hub(token=token, ip_address=hub_ip)
        print(f"Checking IKEA Hub at {hub_ip}...")
        
        # Pulling the specific categories for MYGGBETT and MYGGSPRAY
        get_battery_status(hub.get_open_close_sensors(), "Door/Window Sensors (MYGGBETT)")
        get_battery_status(hub.get_motion_sensors(), "Motion Sensors (MYGGSPRAY)")
        
        # Including your other potential battery devices
        get_battery_status(hub.get_environment_sensors(), "Environment Sensors")
        get_battery_status(hub.get_controllers(), "Remotes & Controllers")
        get_battery_status(hub.get_blinds(), "Smart Blinds")

    except Exception as e:
        print(f"Error connecting to Hub: {e}")

if __name__ == "__main__":
    main()
