crontab -l | grep -v 'ikea_smart_home' | cat - config/crontab.txt | crontab -
