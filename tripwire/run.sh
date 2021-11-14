#!/bin/bash
 
if [ $# -eq 0 ]; then
	python ~/TripWire/tripwire/tripwire.py -bot & 
fi

if [ $# -gt 0 ]; then
	# check for special options
	if [ $1 -eq 1337 ] ; then
		echo '[+] Creating TripWire Cronjob'
		script="bash "$PWD/run.sh" &" 
		echo $script >> /etc/rc.local	
	
	else
		echo 'Installing Python Dependencies'
		pip install discord.py
		pip install python-dotenv
		pip install discord_webhook
	fi
fi

#EOF
