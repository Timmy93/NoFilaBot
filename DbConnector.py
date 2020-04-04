#!/usr/bin/env python3
import sqlite3
import os

#Check if the given path is an absolute path
def createAbsolutePath(path):
	if not os.path.isabs(path):
		currentDir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(currentDir, path)
	return path

# The main class
class DbConnector:
	
	#Load config and psw
	def __init__(self, config, loggingHandler):
		dbName 	= "NoFilaDB.db"
		self.logging = loggingHandler
		
		self.conn = sqlite3.connect(dbName)
		#Initialize db if missing
		if not os.path.isfile(dbName):
			self.createTables()
		self.cursor = self.conn.cursor()
		
		self.logging.info("Db connection created")

	#Create all tables
	def createTables(self):
		self.createContactListTable()
		
	#Create the table to 
	def createContactListTable(self):
		sql = "CREATE TABLE users(chat_id varchar(64))"
		self.cursor.execute(sql)

	#Add an element
	def insertContact(self, chatId):
		sql = "INSERT INTO users values(?)"
		if type(chatId) is not list:
			chatId = [chatId]
		self.cursor.executemany(insertValues, chatId)

	#Retrieve all the users
	def getContacts(self):
		sql = "SELECT * FROM users"
		return self.cursor.execute(insertValues)
