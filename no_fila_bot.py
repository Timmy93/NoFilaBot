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
from TelegramBot2 import TelegramBot2

#Check if the given path is an absolute path
def createAbsolutePath(path):
	if not os.path.isabs(path):
		currentDir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(currentDir, path)
		
	return path

def sendScriptUpdates():
	print("Partito")
	for chat in config['Telegram']['users']:
		tmBot.analyseLog(chat)
		
configFile = "config.yml"
logFile = "TelegramBot.log"
old_log_dir = "old_logs"
configFile = createAbsolutePath(configFile)
logFile = createAbsolutePath(logFile)
old_log_dir = createAbsolutePath(old_log_dir)

#Set logging file
#Update log file if needed
logging.basicConfig(filename=logFile,level=logging.ERROR,format='%(asctime)s %(levelname)-8s %(message)s')
#Load config
with open(configFile, 'r') as stream:
	try:
		config = yaml.safe_load(stream)
		logging.getLogger().setLevel(config['Settings']['logLevel'])
		logging.info('Loaded settings started')
		#Create bot class
		tmBot = TelegramBot2(config, logging)
	except yaml.YAMLError as exc:
		print("Cannot load file: ["+str(configFile)+"] - Error: "+exc)
		logging.error("Cannot load file: ["+str(configFile)+"] - Error: "+exc)
		exit()

#On boot action
if len(sys.argv) > 1 and sys.argv[1]=='systemd':
    logging.info("Started by systemd using argument: "+sys.argv[1])
tmBot.rebootAlert()
#Scheduling
for t in config['LogCollector']['times']:
	schedule.every().day.at(t).do(sendScriptUpdates)

tmBot.start()
print('Bot is now listening...')
logging.info("Bot started succesfully")

while 1:
		time.sleep(1)
		schedule.run_pending()
