#!/usr/bin/env python3
import os
import logging
import yaml
from random import randint
from time import sleep
import requests
import tailer
import string
from datetime import datetime
import telepot


#Provide useful functionalities to handle a Telegram message
class TelegramMessage:
	
	def __init__(self, message, loggingHandler):
		self.logging = loggingHandler
		self.message = message
		self.content_type, self.chat_type, self.chat_id = telepot.glance(self.message)
		self.handleMessage()
		
	#Check if this type of messages is supported
	def handleMessage(self):
		if self.isText():
			text = self.message['text']
			self.logging.info("Handling textual message: "+text)
		else:
			self.logging.warning('Cannot handle this type of message: '+content_type)
	
	#Check if the message is textual	
	def isText(self):
		return self.content_type == 'text';
	
	#Check if the message has a certain text
	def hasThisText(self, text):
		return text.strip() == self.message['text'].strip()
	
	#Get the message text
	def getText(self):
		return self.message['text'].strip()
	
	#Return the chat id
	def getChat(self):
		return self.chat_id;
	
class LogReadingException(Exception):
    pass	
