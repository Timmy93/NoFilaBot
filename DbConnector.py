#!/usr/bin/env python3
import sqlite3
import os

# The main class
class DbConnector:
	
	#Load config and psw
	def __init__(self, dbPath, loggingHandler):
		self.dbName = dbPath
		self.logging = loggingHandler
		dbToInitialize = self.dbExists()
				
		#Initialize db if missing
		if not dbToInitialize:
			self.createTables()
			self.logging.info("All tables created")
	
	def dbExists(self):
		return os.path.isfile(self.dbName)

	#Create all tables
	def createTables(self):
		#Start connection
		conn = sqlite3.connect(self.dbName)
		cursor = conn.cursor()
		self.logging.info("Db connected")
		#Create here tables
		self.createContactListTable(cursor)
		#Close connection
		conn.commit()
		conn.close()
		
	#Create the table to store the chat
	def createContactListTable(self, cursor):
		sql = "CREATE TABLE users(chat_id varchar(64), UNIQUE(chat_id))"
		cursor.execute(sql)

	#Add an element
	def insertContact(self, chatId):
		#Start connection
		conn = sqlite3.connect(self.dbName)
		cursor = conn.cursor()
		self.logging.info("Db connected")
		sql = "INSERT OR IGNORE INTO users values(?)"
		if type(chatId) is not list:
			chatId = [str(chatId)]
		cursor.executemany(sql, [chatId])
		#Close connection
		conn.commit()
		conn.close()

	#Delete an element
	def removeContact(self, chatId):
		#Start connection
		conn = sqlite3.connect(self.dbName)
		cursor = conn.cursor()
		self.logging.info("Db connected")
		#Execute
		sql = "DELETE FROM users where chat_id = ?"
		if type(chatId) is not list:
			chatId = [str(chatId)]
		cursor.executemany(sql, [chatId])
		#Close connection
		conn.commit()
		conn.close()

	#Retrieve all the users
	def getContacts(self):
		#Start connection
		conn = sqlite3.connect(self.dbName)
		cursor = conn.cursor()
		self.logging.info("Db connected")
		#Execute
		sql = "SELECT * FROM users"
		c_list = cursor.execute(sql)
		c_list = c_list.fetchall()
		#Close connection
		conn.commit()
		conn.close()
		return c_list
