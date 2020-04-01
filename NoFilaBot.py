#!/usr/bin/env python3
import json
import os
import logging
import yaml
from time import sleep
import requests
import string
from datetime import datetime
import sys
import subprocess
import random
import time
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from subprocess import call

#Check if the given path is an absolute path
def createAbsolutePath(path):
	if not os.path.isabs(path):
		currentDir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(currentDir, path)
		
	return path

# The main class
class NoFilaBot:
	
	#Load config and psw
	def __init__(self, config, loggingHandler):
		all_settings_dir 	= "Settings"
		contact_list_path	= "myContactList.json"
		
		self.config = config
		self.logging = loggingHandler
		
		#Loading values
		self.localParameters = config['local']
		self.serverInfo = config['server']
		self.mySupermarkets = config['supermarkets']
		self.mySupermarketsList = self.getMySuperMarket()
		self.logging.info('Supermarkets list extracted')
		self.readContactList(createAbsolutePath(os.path.join(all_settings_dir,contact_list_path)))
		
		#Connecting to Telegram
		self.TmUpdater = Updater(self.localParameters['telegram_token'], use_context=True)
		self.TmDispatcher = self.TmUpdater.dispatcher
		self.bot = self.TmUpdater.bot
		self.logging.info("Connected succesfully to Telegram")

	#Read my contact list
	def readContactList(self, path):
		try:
			with open(path) as json_file:
				self.myContactList = json.load(json_file)
		except ValueError:
			self.logging.warning('Cannot decode the stored contact list - Using an empty one')
			print("Invalid json ["+str(path)+"] - Use empty one")
			self.myContactList = []
		except FileNotFoundError:
			self.logging.warning('Stored contact list not found- Using an empty one')
			print("Contact list not existet ["+str(path)+"] - Use empty one")
			self.myContactList = []
		self.logging.info('Contact list loaded')
		return self.myContactList
	
	#The complete function that iterate over all values
	def updateStatus(self):
		self.logging.info('Starting periodic update')
		sm = self.requestUpdateSupermarkets()
		self.logging.info('Update received')
		relevant = self.parseAllSupermarkets(sm)
		self.logging.info('Found '+str(len(relevant))+' relevant updates')
		for relSup in relevant:
			self.sendNotify(relSup['name'], relSup['minutes'], relSup['people'])
		if not len(relevant):
			self.sendNotify("Nessun aggiornamento rilevante, continuo a monitorare")
		
	#Send the request to the server to update the list of open supermarket
	def requestUpdateSupermarkets(self):
		payload = {'lat': self.serverInfo['lat'], 'long': self.serverInfo['long'], 'debug': self.serverInfo['debug']}
		h = {
			'User-Agent': self.serverInfo['user_agent'],
			'Accept': 'application/json, text/javascript, */*; q=0.01',
			'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
			'Content-Type': 'application/json',
			'Origin': 'https://filaindiana.it',
			'Referer': 'https://filaindiana.it/' 
		}
		r = requests.post(self.serverInfo['server_url'], data=json.dumps(payload), headers=h)
		# ~ r = requests.post(self.serverInfo['server_url'], data=json.dumps(payload))
		
		# ~ self.logging.info(str(payload))
		# ~ self.logging.info(str(self.serverInfo['server_url']))
		# ~ self.logging.info("Response received ["+r.text+"]")
		
		return r.json()
		
	#Parse all the give supermarkets to discover relevant updates
	def parseAllSupermarkets(self, dct):
		relevant = []
		for sm in dct:
			if 'state' in sm and (sm['state']['queue_wait_minutes'] < self.localParameters['max_wait'] or sm['state']['queue_size_people'] < self.localParameters['max_people']):
				lastUpdate = self.parseTime(sm['state']['updated_at'])
				elapsed = datetime.now() - lastUpdate
				#Check if enough time has passed
				if elapsed.total_seconds() < self.localParameters['refresh_rate']*60:
					#Check if enough time has passed
					relevant.append({
						'name': sm['supermarket']['market_id'], 
						'minutes': sm['state']['queue_wait_minutes'], 
						'people': sm['state']['queue_size_people']
					})
				else:
					self.logging.info("Elapsed "+str(elapsed.total_seconds())+" seconds from last update - Skip")
			else:
				if not 'state' in sm:
					self.logging.info("This supermarket has never received an update")
				else:
					self.logging.info("Supermarket - People: "+str(sm['state']['queue_size_people'])+" - Wait: "+str(sm['state']['queue_wait_minutes']))
		return relevant
	
	#Parse the time in the log
	def parseTime(self, timeString):
		timeFormat = '%Y-%m-%d %H:%M:%S'
		parsed = datetime.strptime(timeString, timeFormat)
		return parsed
	
	#Extract list of my supermarkes
	def getMySuperMarket(self):
		return dict((i['market_id'], i['user_friendly_name']) for i in self.mySupermarkets)
	
	#Notify all open chat with this bot	
	def sendNotify(self, supermarket, minutes, people):
		for user in self.myContactList:
			self.sendMessage(
				self.mySupermarketsList[supermarket]+" - Circa "+str(people)+" persone in fila (stimati "+str(minutes)+" minuti di coda)",
				user
			)
			self.logging.info('Notify sent to '+str(user))
			
	#Send the selected message
	def sendMessage(self, message, chat=None):
		mex = str(message)[:4095]
		if not chat:
			chat = self.message.getChat()
		self.bot.sendMessage(chat, mex)
	
	#Enable the deamon to answer to message
	def start(self):
		#Defining handlers
		self.createHandlers()
		self.logging.info("Bot handlers created")
		print("Bot handlers created")
		#Starting bot
		self.TmUpdater.start_polling()
		self.logging.info("Bot is now polling for new messages")
		
		#No need to put the bot in idle
		# ~ self.TmUpdater.idle()
	
	#Define the approriate handlers
	def createHandlers(self):
		#Commands
		self.TmDispatcher.add_handler(CommandHandler("start", self.welcomeMessage))
		self.logging.info("createHandlers - Created handlers for command")
		#Text message
		self.TmDispatcher.add_handler(MessageHandler(Filters.text, self.manageText))
		self.logging.info("createHandlers - Created handlers for text")
	
	#Handle a received message
	def manageText(self, msg):
		self.loggin.info("Received text message - Ignoring")
		print("Press /start to enable this bot")
	
	#Answers with a welcome message
	def welcomeMessage(self, update=None, context=None):
		self.logging.info("welcomeMessage - Bot started by: "+str(update.effective_chat))
		if update.effective_chat.id in self.myContactList:
			update.message.reply_text("Bentornato " + str(update.effective_chat.first_name))
		else:
			self.myContactList.append(update.effective_chat.id)
			update.message.reply_text("Ciao "+str(update.effective_chat.first_name)+", da adesso sarai aggiornati sulla fila dei supermercati nei dintorni")
