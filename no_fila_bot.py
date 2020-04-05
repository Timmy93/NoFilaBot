#!/usr/bin/env python3
import sys
import os
import logging
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
import threading
from NoFilaBot import NoFilaBot

#Check if the given path is an absolute path
def createAbsolutePath(path):
	if not os.path.isabs(path):
		currentDir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(currentDir, path)
		
	return path

#Used to run scheduled task as threads
def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

#Defining local parameters
all_settings_dir 	= "Settings"
local_path 			= "local_settings.json"
server_path 		= "server_settings.json"
monitored_path 		= "monitored_market.json"
logFile		 		= "NoFilaBot.log"
local_path 			= createAbsolutePath(os.path.join(all_settings_dir, local_path))
server_path 		= createAbsolutePath(os.path.join(all_settings_dir, server_path))
monitored_path 		= createAbsolutePath(os.path.join(all_settings_dir, monitored_path))
logFile 			= createAbsolutePath(logFile)

#Set logging file
#Update log file if needed
logging.basicConfig(filename=logFile,level=logging.ERROR,format='%(asctime)s %(levelname)-8s %(message)s')

#Load config
config = dict()
try:
	path = local_path
	with open(path) as json_file:
		config['local']			= json.load(json_file)
	path = server_path
	with open(path) as json_file:
		config['server'] 		= json.load(json_file)
	path = monitored_path
	with open(path) as json_file:
		config['supermarkets'] 	= json.load(json_file)
except ValueError:
	print("Cannot load settings - Invalid json ["+str(path)+"]")
	exit()
except FileNotFoundError:
	print("Cannot load settings - Setting file not found ["+str(path)+"]")
	exit()

logging.getLogger().setLevel('INFO')
nfb = NoFilaBot(config, logging)

#On boot action
if len(sys.argv) > 1 and sys.argv[1]=='systemd':
    logging.info("Started by systemd using argument: "+sys.argv[1])

#Schedule actions
schedule.every(config['local']['refresh_rate']).minutes.do(run_threaded, nfb.updateStatus)
logging.info("Update every "+str(config['local']['refresh_rate'])+" minutes")
# ~ schedule.every().minutes.do(nfb.updateStatus)

#Start bot
nfb.start()

#DELETE - FOR Debug only
run_threaded(nfb.updateStatus(disableNotify=True))
# ~ exit()


print('Bot started succesfully')
logging.info("Bot started succesfully")

while 1:
	time.sleep(1)
	schedule.run_pending()
