import os
from dotenv import load_dotenv
from dirigera import Hub

# Load credentials
load_dotenv()
token = os.getenv("DIRIGERA_TOKEN")
hub_ip = os.getenv("DIRIGERA_IP") # 

def get_battery_status(devices, category_name):
    print(f"\n--- {category_name} ---")
    found = False
    
    # Sort devices by room name to keep things organized
    for d in devices:
        battery = getattr(d.attributes, "battery_percentage", None)
        
        if battery is not None:
            found = True
            name = d.attributes.custom_name
            # Get the room name safely
            room = d.room.name if hasattr(d, "room") and d.room else "Unassigned"
            
            # Simple status logic
            status = "OK"
            if battery < 20:
                status = "LOW!"
            elif battery < 10:
                status = "CRITICAL"
                
            # Formatting: Room (15 chars) | Name (25 chars) | Battery | Status
            print(f"{room:<13} | {name:<30} | {battery:>3}% | {status}")
    
    if not found:
        print("No battery-powered devices found in this category.")

def main():
    if not hub_ip or not token:
        print("Error: DIRIGERA_HUB or DIRIGERA_TOKEN not found in .env file.")
        return

    try:
        hub = Hub(token=token, ip_address=hub_ip)
        print(f"Checking IKEA Hub at {hub_ip}...")
        
        # Pulling categories
        get_battery_status(hub.get_environment_sensors(), "Environment Sensors")
        get_battery_status(hub.get_controllers(), "Remotes & Controllers")
        get_battery_status(hub.get_blinds(), "Smart Blinds")

    except Exception as e:
        print(f"Error connecting to Hub: {e}")

if __name__ == "__main__":
    main()
