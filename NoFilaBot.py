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
from TelegramMessage import TelegramMessage

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
		self.config = config
		self.logging = loggingHandler
		
		#Loading values
		self.readLocalParameters(config['local'])
		self.readServerParameters(config['server'])
		self.readMySupermarket(config['supermarkets'])
		
		#Connecting to Telegram
		self.TmUpdater = Updater(self.localParameters['telegram_token'], use_context=True)
		self.TmDispatcher = self.TmUpdater.dispatcher
		self.bot = self.TmUpdater.bot
		self.logging.info("Connected succesfully to Telegram")
	
	#Read local parameters
	def readLocalParameters(self, path):
		self.localParameters = json.load(path)
		self.logging.info('Local settings loaded')
		return self.localParameters
	
	#Read the server parameters
	def readServerParameters(self, path):
		self.serverInfo = json.load(path)
		self.logging.info('Server settings loaded')
		return self.serverInfo
	
	#Read the personal list of supermarket
	def readMySupermarket(self, path):
		self.mySupermarkets = json.load(path)
		self.logging.info('My supermarkets loaded')
		self.mySupermarketsList = self.getMySuperMarket()
		self.logging.info('Supermarkets list extracted')
		return self.mySupermarkets
	
	#Read my contact list
	def readContactList(self, path):
		self.myContactList = json.load(path)
		self.logging.info('My contact list loaded')
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
		
	#Send the request to the server to update the list of open supermarket
	def requestUpdateSupermarkets(self):
		payload = {'lat': self.serverInfo['lat'], 'long': self.serverInfo['long'], 'debug': self.serverInfo['debug']}
		headers = {
			'User-Agent': self.serverInfo['user_agent'],
			'Accept': 'application/json, text/javascript, */*; q=0.01' 
			'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3' 
			'Content-Type': 'application/json' 
			'Origin': 'https://filaindiana.it' 
			'Referer': 'https://filaindiana.it/' 
		}
		r = requests.get(self.serverInfo['server_url'], params=payload)
		return r.json()
		
	#Parse all the give supermarkets to discover relevant updates
	def parseAllSupermarkets(self, dct):
		relevant = []
		for sm in dct:
			if 'state' in dct and (sm['state']['queue_wait_minutes'] < self.localParameters['max_wait'] or sm['state']['queue_size_people'] < self.localParameters['max_people']):
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
		return relevant
	
	#Parse the time in the log
	def parseTime(self, timeString):
		timeFormat = '%Y-%m-%d %H:%M:%S.%f'
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
		print("Handlers created!")
		#Starting bot
		self.TmUpdater.start_polling()
		self.logging.info("Bot is now polling for new messages")
		
		#No need to put the bot in idle
		# ~ self.TmUpdater.idle()
	
	#Define the approriate handlers
	def createHandlers(self):
		#Commands
		self.TmDispatcher.add_handler(CommandHandler("start", self.welcomeMessage))
		self.TmDispatcher.add_handler(CommandHandler("reboot", self.rebootHandler))
		self.TmDispatcher.add_handler(CommandHandler("log", self.logHandler))
		self.logging.info("createHandlers - Created handlers for command")
		#Text message
		self.TmDispatcher.add_handler(MessageHandler(Filters.text, self.searchHandler))
		self.logging.info("createHandlers - Created handlers for text")
	
	#Handle a received message
	def handleMessage(self, msg):
		self.message = TelegramMessage(msg, self.logging)
		if self.message.isText():
			self.handleTextMessage()
		
	#Handle different text messages
	def handleTextMessage(self):
		if self.message.hasThisText("/start"):
			self.welcomeMessage()
		elif self.message.hasThisText("/reboot") and self.isAdmin(self.message.getChat()):
			self.sendMessage("Riavvio...")
			risultato = str(subprocess.Popen("sudo reboot", shell=True, stdout=subprocess.PIPE).stdout.read())
		elif self.message.hasThisText("/log") and self.isAdmin(self.message.getChat()):
			self.analyseLog()
		else:
			releases = self.getRelease(self.message.getText())
			self.printReleases(self.message.getChat(), releases)	
	
	#Answers with a welcome message
	def welcomeMessage(self, update=None, context=None):
		self.logging.info("welcomeMessage - Bot started by: "+str(update.effective_chat))
		if update.effective_chat.id in self.myContactList:
			update.message.reply_text("Bentornato " + str(update.effective_chat.first_name))
		else:
			#Sleep to avoid misuse of the bot
			#time.sleep(2)
			update.message.reply_text("Ciao "+str(update.effective_chat.first_name)+", da adesso sarai aggiornati sulla fila dei supermercati nei dintorni")
		
	#Search a predefined release
	def getRelease(self, title):
		return self.apiHandler.searchRelease(title)
