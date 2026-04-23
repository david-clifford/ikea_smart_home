Exploratory project to connect to my DIRIGERA hub, activate a smart plug and read environmental sensor data.

Follow the instructions at https://github.com/Leggin/dirigera#quickstart for how to set up two environment variables
 - DIRIGERA_TOKEN
 - DIRIGERA_IP

Scripts
 - outlets_test.py - finds my smart outlet, turns it on for 15s, then off. Make sure something like a light / radio is attached to confirm this works
 - list_sensors.py - lists the various environmental sensors and their associated sensor values (temperature, CO2, relative humidity etc)
 - battery_check.py - return the battery percentage reading for each sensor

Ideas / To Do:
 - Read the archive of temperature data stored on the hub
 - Plot that information and make it available elsewhere 
