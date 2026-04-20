import os
import time
from dotenv import load_dotenv
from dirigera import Hub

# 1. Load credentials from your .env file
load_dotenv()
token = os.getenv("DIRIGERA_TOKEN")
hub_ip = os.getenv("DIRIGERA_IP")

def main():
    try:
        # 2. Connect and confirm
        hub = Hub(token=token, ip_address=hub_ip)
        
	# Fetching a small detail to verify the connection is alive
        print(f"--- Connected to IKEA Hub at {hub_ip} ---")

        # 3. List all outlets in the system
        print("\nSearching for outlets...")
        outlets = hub.get_outlets()
        
        if not outlets:
            print("No outlets found in this system.")
            return

        print(f"Found {len(outlets)} outlet(s):")
        for o in outlets:
            print(f" - {o.attributes.custom_name} (Status: {'ON' if o.attributes.is_on else 'OFF'})")

        # 4. Targeted Action on P1
        target_name = "P1"
        outlet = hub.get_outlet_by_name(target_name)

        if outlet:
            print(f"\n--- Sequence Started for {target_name} ---")
            
            print(f"Action: Turning {target_name} ON...")
            outlet.set_on(outlet_on=True)
            
            print("Timer: Sleeping for 15 seconds...")
            time.sleep(15)
            
            print(f"Action: Turning {target_name} OFF...")
            outlet.set_on(outlet_on=False)
            
            print("--- Sequence Complete ---")
        else:
            print(f"\nError: Could not find an outlet named '{target_name}'.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
