import os
from dotenv import load_dotenv
from dirigera import Hub

# Load credentials
load_dotenv()
token = os.getenv("DIRIGERA_TOKEN")
hub_ip = os.getenv("DIRIGERA_IP")

def main():
    try:
        hub = Hub(token=token, ip_address=hub_ip)
        print(f"--- Connected to IKEA Hub: {hub_ip} ---")

        sensors = hub.get_environment_sensors()
        
        if not sensors:
            print("No environment sensors found.")
            return

        # Header with 30-space padding for Name
        header = f"{'DEVICE NAME':<30} | {'TEMP':<8} | {'HUMIDITY':<10} | {'PM2.5':<8} | {'CO2':<8} |"
        print("\n")
        print("-" * len(header))
        print(f"{header}")
        print("-" * len(header))

        # This loop MUST be indented under the 'try'
        for s in sensors:
            attrs = s.attributes
            name = attrs.custom_name
            
            # Temperature
            temp = attrs.current_temperature
            temp_str = f"{round(temp, 1)}°C" if temp is not None else "--"
            
            # Humidity
            rh = attrs.current_r_h
            rh_str = f"{round(rh, 1)}%" if rh is not None else "--"
            
            # PM 2.5
            pm25 = attrs.current_p_m25
            pm25_str = f"{round(pm25, 1)}" if pm25 is not None else "--"

            # CO2
            co2 = attrs.current_c_o2
            co2_str = f"{int(co2)}" if co2 is not None else "--"
            
            print(f"{name:<30} | {temp_str:<8} | {rh_str:<10} | {pm25_str:<8} | {co2_str:<8} |")

        print("-" * len(header))
        print("\n")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
