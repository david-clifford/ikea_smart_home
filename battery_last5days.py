import sqlite3
con = sqlite3.connect('readings.db')
for r in con.execute('''
    SELECT datetime(timestamp, \"localtime\"), sensor, room, reading_type, value
    FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY sensor ORDER BY timestamp DESC) AS rn FROM readings WHERE reading_type = \"battery\")
    WHERE rn <= 5
    ORDER BY room, timestamp ASC
'''): print(r)

