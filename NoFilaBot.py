#!/usr/bin/env python3
import json
import os
import logging
from time import sleep
import requests
import string
from datetime import datetime
import sys
import subprocess
import random
import time
import json
import telegram
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
		self.contactListPath = createAbsolutePath(os.path.join(all_settings_dir,contact_list_path))
		self.readContactList()
		self.smCache = {}
		
		#Connecting to Telegram
		self.TmUpdater = Updater(self.localParameters['telegram_token'], use_context=True)
		self.TmDispatcher = self.TmUpdater.dispatcher
		self.bot = self.TmUpdater.bot
		self.logging.info("Connected succesfully to Telegram")

	#Read my contact list
	def readContactList(self):
		try:
			with open(self.contactListPath) as json_file:
				self.myContactList = json.load(json_file)
		except ValueError:
			self.logging.warning('Cannot decode the stored contact list - Using an empty one')
			print("Invalid json ["+str(self.contactListPath)+"] - Use empty one")
			self.myContactList = []
		except FileNotFoundError:
			self.logging.warning('Stored contact list not found - Using an empty one')
			print("Contact list not existent ["+str(self.contactListPath)+"] - Using an empty one")
			self.myContactList = []
		self.logging.info('Contact list loaded')
		return self.myContactList
	
	#Updates the contact list
	def storeContactList(self):
		with open(self.contactListPath, "w") as json_file:
				json.dump(self.myContactList, json_file)
	
	#Enable the deamon to answer to message
	def start(self):
		#Defining handlers
		self.createHandlers()
		self.logging.info("Bot handlers created")
		print("Bot handlers created")
		#Starting bot
		self.TmUpdater.start_polling()
		self.logging.info("Bot is now polling for new messages")
	
		#The complete function that iterate over all values
	def updateStatus(self, useCache = False, peopleToNotify = None):
		self.logging.info('Starting periodic update')
		if peopleToNotify is None:
			#If no specific user are defined broadcast the message
			peopleToNotify = self.myContactList
		elif type(peopleToNotify) is not list:
			#If passed a single user transform to list
			peopleToNotify = [peopleToNotify]
		
		#Check if is requested to notify someone
		if not len(peopleToNotify):
			self.logging.info('No one to update - Skip refresh')
			return
		
		#Check if a cache refresh is needed
		if not useCache or len(peopleToNotify) < 1:
			self.smCache = self.requestUpdateSupermarkets()
			self.logging.info('Cache refreshed')
		
		#Parse data
		relevant = self.parseAllSupermarkets(self.smCache)
		self.logging.info('Found '+str(len(relevant))+' relevant updates')
		
		#Send the notify to subscribed users
		for relSup in relevant:
			for user in peopleToNotify:
				self.sendNotify(user, relSup['name'], relSup['minutes'], relSup['people'])
		
		
	#Send the request to the server to update the list of open supermarket
	def requestUpdateSupermarkets(self):
		payload = {
			'lat': self.localParameters['lat'], 
			'long': self.localParameters['long'], 
			'debug': self.serverInfo['debug']
		}
		h = {
			'User-Agent': self.serverInfo['user_agent'],
			'Accept': 'application/json, text/javascript, */*; q=0.01',
			'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
			'Content-Type': 'application/json',
			'Origin': 'https://filaindiana.it',
			'Referer': 'https://filaindiana.it/' 
		}
		r = requests.post(self.serverInfo['server_handler'], data=json.dumps(payload), headers=h)
		return r.json()
		
	#Parse all the give supermarkets to discover relevant updates
	def parseAllSupermarkets(self, dct):
		relevant = []
		for sm in dct:
			if 'state' in sm and (sm['state']['queue_wait_minutes'] < self.localParameters['max_wait'] or sm['state']['queue_size_people'] < self.localParameters['max_people']):
				lastUpdate = self.parseTime(sm['state']['updated_at'])
				elapsed = datetime.now() - lastUpdate
				#Check if enough time has passed
				if elapsed.total_seconds() < self.localParameters['max_age']*60:
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
	def sendNotify(self, user, supermarket, minutes, people):
		self.logging.info('Sending update to: '+str(user))
		if supermarket in self.mySupermarketsList.keys():
			self.sendMessage(
				"*"+self.getSupermarketName(supermarket)+"* \- Circa *"+str(people)+" persone* in fila \(stimati "+str(minutes)+" minuti di coda\)",
				user,
				telegram.ParseMode.MARKDOWN_V2
			)
			self.logging.info('Notify sent to '+str(user))
		else:
			self.logging.info('Ignoring this supermarket ['+supermarket+']')			
	
	#Extract the supermarket from the given list
	def getSupermarketName(self, supermarket):
		return str(self.mySupermarketsList[supermarket]).replace("-", "\-")	
		
	#Send the selected message
	def sendMessage(self, message, chat=None, parse_mode=None):
		mex = str(message)[:4095]
		if not chat:
			self.logging.error("Missing chat - Message not sent")
			return
		self.bot.sendMessage(chat, mex, parse_mode=parse_mode)
	
	#Define the approriate handlers
	def createHandlers(self):
		#Commands
		self.TmDispatcher.add_handler(CommandHandler("start", self.startHandler))
		self.TmDispatcher.add_handler(CommandHandler("stop", self.stopHandler))
		self.TmDispatcher.add_handler(CommandHandler("report", self.reportHandler))
		self.logging.info("createHandlers - Created handlers for command")
		#Text message
		self.TmDispatcher.add_handler(MessageHandler(Filters.text, self.textHandler))
		self.logging.info("createHandlers - Created handlers for text")
	
	#Handle a received message
	def textHandler(self, update=None, context=None):
		self.logging.info("Received text message - Ignoring")
		update.message.reply_text("Press /start to enable this bot")
	
	#Start the subscription to the bot
	def startHandler(self, update=None, context=None):
		self.logging.info("startHandler - Bot started by: "+str(update.effective_chat))
		if update.effective_chat.id in self.myContactList:
			update.message.reply_text("Ciao " + str(update.effective_chat.first_name) + ", controllo se ci sono nuove segnalazioni")
		else:
			self.myContactList.append(update.effective_chat.id)
			self.storeContactList()
			update.message.reply_text("Ciao "+str(update.effective_chat.first_name)+", da adesso sarai aggiornati sulla fila dei supermercati nei dintorni. Premi /stop per non ricevere più notifiche")
		self.updateStatus(useCache=True, peopleToNotify=update.effective_chat.id)

	#Stop the subscription to the bot
	def stopHandler(self, update=None, context=None):
		self.logging.info("stopHandler - Bot stopped by: "+str(update.effective_chat))
		if update.effective_chat.id in self.myContactList:
			self.myContactList.remove(update.effective_chat.id)
			self.storeContactList()
			self.logging.info("stopHandler - "+str(update.effective_chat.id)+" removed from contact list")
		update.message.reply_text("Ciao "+str(update.effective_chat.first_name)+", smetto di inviarti notifiche. Premi /start per ricominciare ad essere aggiornato")
	
	#Used to report the supermarket queue status
	def reportHandler(self, update=None, context=None):
		self.logging.info("reportHandler - Report requested by: "+str(update.effective_chat))
		update.message.reply_text(
			"Visita ["+self.serverInfo['report_site_name']+"]("+self.serverInfo['report_site_url']+") per inviare le segnalazioni",
			parse_mode=telegram.ParseMode.MARKDOWN_V2
		)
