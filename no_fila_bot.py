#!/usr/bin/env python3
import sys
import os
import logging
import yaml
import subprocess
import time
import random
import datetime
import time
from telegram.ext import Updater
import json
import requests
from subprocess import call
import schedule
from NoFilaBot import NoFilaBot

#Check if the given path is an absolute path
def createAbsolutePath(path):
	if not os.path.isabs(path):
		currentDir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(currentDir, path)
		
	return path

#Defining local parameters
all_settings_dir 	= "Settings"
local_path 			= "local_settings.json"
server_path 		= "server_settings.json"
monitored_path 		= "monitored_markets.json"
logFile		 		= "NoFilaBot.json"
local_path 			= createAbsolutePath(os.path.join("all_settings_dir", local_path))
server_path 		= createAbsolutePath(os.path.join("all_settings_dir", server_path))
monitored_path 		= createAbsolutePath(os.path.join("all_settings_dir", monitored_path))
logFile 			= createAbsolutePath(logFile)

#Set logging file
#Update log file if needed
logging.basicConfig(filename=logFile,level=logging.ERROR,format='%(asctime)s %(levelname)-8s %(message)s')

#Load config
config['local']			= json.load(local_path)
config['server'] 		= json.load(server_path)
config['supermarkets'] 	= json.load(monitored_path)

nfb = NoFilaBot(config, logging)

#On boot action
if len(sys.argv) > 1 and sys.argv[1]=='systemd':
    logging.info("Started by systemd using argument: "+sys.argv[1])

#Schedule actions
schedule.every(config['local']['refresh_rate']).minutes.do(nfb.updateStatus())

#Start bot
nfb.start()
print('Bot started succesfully')
logging.info("Bot started succesfully")

while 1:
	time.sleep(1)
	schedule.run_pending()
