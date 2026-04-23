import os
from dotenv import load_dotenv
from dirigera import Hub

# Load credentials
load_dotenv()
token = os.getenv("DIRIGERA_TOKEN")
hub_ip = os.getenv("DIRIGERA_IP")

def get_battery_status(devices, category_name):
    print(f"\n--- {category_name} ---")
    found = False
    for d in devices:
        # Check if the device has a battery attribute
        battery = getattr(d.attributes, "battery_percentage", None)
        
        if battery is not None:
            found = True
            name = d.attributes.custom_name
            # Color coding: Simple visual warning for low battery
            status = "OK"
            if battery < 20:
                status = "LOW!"
            elif battery < 10:
                status = "CRITICAL"
                
            print(f"{name:<30} | {battery:>3}% | {status}")
    
    if not found:
        print("No battery-powered devices found in this category.")

def main():
    try:
        hub = Hub(token=token, ip_address=hub_ip)
        print(f"Checking IKEA Hub at {hub_ip} for battery levels...")

        # Dirigera separates devices by type, so we check the most common ones
        get_battery_status(hub.get_environment_sensors(), "Environment Sensors")
        get_battery_status(hub.get_controllers(), "Remotes & Controllers")
        get_battery_status(hub.get_blinds(), "Smart Blinds")

    except Exception as e:
        print(f"Error connecting to Hub: {e}")

if __name__ == "__main__":
    main()
