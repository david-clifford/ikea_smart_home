CURRENT STATUS - I ended up returning the system of sensors to IKEA due to persistent network crashes requiring setting everything up from scratch sensor by sensor. Adding sensors one by one, each one requiring several attempts via their app was a terrible user experience. 

Exploratory project to connect to my DIRIGERA hub, activate a smart plug and read environmental sensor data.

Follow the instructions at https://github.com/Leggin/dirigera#quickstart for how to set up two environment variables
 - DIRIGERA_TOKEN
 - DIRIGERA_IP

Also include environmental variables for communicating with the system via telegram and receiving quickchart images. 
 - TELEGRAM_BOT_TOKEN
 - TELEGRAM_USER_ID
 - QUICKCHART_URL


Scripts
 - outlets_test.py - finds my smart outlet, turns it on for 15s, then off. Make sure something like a light / radio is attached to confirm this works
 - list_sensors.py - lists the various environmental sensors and their associated sensor values (temperature, CO2, relative humidity etc)
 - battery_check.py - return the battery percentage reading for each sensor
 - hub.py - boiler plate functions to connect to the hub, collect battery and sensor values, write to our DB
 - config/ - config files for cron jobs and log rotations. Run ```bash config/install_cron.sh``` whenever those settings need to change

To set up on a fresh machine (or after changes), just:
```
bash config/install_cron.sh
sudo cp config/ikea_smart_home.logrotate /etc/logrotate.d/ikea_smart_home
```

Ideas / To Do:
 - Read the archive of temperature data stored on the hub
 - Plot that information and make it available elsewhere 

Notes:  
 - Timestamps are recorded in UTC. Per Claude I should stick with UTC rather than recording local time for a few reasons:
 - *No ambiguity* — local time has a gap and an overlap every year at DST transitions. A 1:30am reading in October could exist twice.
 - *Easier joins* — if you ever combine this data with other sources (weather APIs, energy data), they'll almost certainly be in UTC.
 - *Display is separate from storage* — you can always convert to local time when querying or plotting

Example Query:
```
python3 -c "
import sqlite3
con = sqlite3.connect('readings.db')
for r in con.execute('SELECT datetime(timestamp, \"localtime\"), sensor, room, reading_type, value FROM readings WHERE reading_type = \"battery\" ORDER BY room, timestamp ASC LIMIT 20'): print(r)
"
```
