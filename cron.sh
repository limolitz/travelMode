#!/bin/bash

# change this to the projects path
# and then copy this file to /etc/NetworkManager/dispatcher.d/90travelMode
# don't copy, unless you have this project saved somewhere as root
cd /home/florin/projekte/travelMode


sudo -u florin LC_ALL=C.UTF-8 DISPLAY=:0.0 python3 travelMode.py >> cron.log 2>>cron.err.log
