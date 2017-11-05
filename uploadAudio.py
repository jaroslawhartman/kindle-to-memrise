#!/usr/bin/env python3

import os
import re
import sys
import argparse
import sqlite3
import json

from urllib.request import urlopen
from urllib.request import urlretrieve

import requests

from bs4 import BeautifulSoup

# cookeis file exported from EditThisCookie chrome extension in format:
# cookies = [
# {
#    "domain": ".memrise.com",
#    "expirationDate": 1541160876,
#    "hostOnly": false,
#    "httpOnly": false,
#    "name": "ajs_anonymous_id",
#    "path": "/",
#    "sameSite": "no_restriction",
#    "secure": false,
#    "session": false,
#    "storeId": "0",
#    "value": "xxxxxx",
#    "id": 1
#},
#
# Manual changes in the file:
#  - add "cookies = " in begginning of the 1st line
#  - change true -> True
#  - change false -> False

from variables import cookies

MEMRISE_ENDPOINT = "https://www.memrise.com/course/"
MEMRISE_LEVEL_ENDPOINT = "https://www.memrise.com/ajax/level/editing_html/?level_id="
MEMRISE_UPLOAD_ENDPOINT = "https://www.memrise.com/ajax/thing/cell/upload_file/"

class DatabaseManager(object):
	def __init__(self, db):
		self.conn = sqlite3.connect(db)
		self.conn.execute('pragma foreign_keys = on')
		self.conn.commit()
		
		self.cur = self.conn.cursor()
	
	def query(self, *arg):
		self.cur.execute(*arg)
		self.conn.commit()
		return self.cur
	
	def close(self):
		self.conn.close()		

	def __del__(self):
		self.conn.close()
	
class CookiesJar(object):
	def __init__(self):
		print("Initialising cookies jar")
		
		self.cookies = requests.cookies.RequestsCookieJar()

		for cookie in cookies:
			self.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
			
	def getCookieValue(self, name):
		for cookie in cookies:
			if(cookie['name'] == name):
				return cookie['value']
		return None

def getAudioFilename(dictionaryDB, word):
	try:
		audioFilename = dictionaryDB.query("SELECT audiofilePath FROM dictionary WHERE word=? AND audiofilePath is not null", [word]).fetchone()[0]
	except:
		print("Audio file for %s not found!" % word)
		return None
	
	return audioFilename
	
def uploadFileToServer(thing_id, cell_id, memriseEditURL, filename, jar):
	files = {'f': ('whatever.mp3', open(filename, 'rb'), 'audio/mp3')}
	
	form_data = { 
		"thing_id": thing_id, 
		"cell_id": cell_id, 
		"cell_type": "column",
		"csrfmiddlewaretoken": jar.getCookieValue('csrftoken')}
	
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0",
		"referer": memriseEditURL}
	
	r = requests.post(MEMRISE_UPLOAD_ENDPOINT, files=files, cookies=jar.cookies, headers=headers, data=form_data, timeout=60)
	
	if not r.status_code == requests.codes.ok:
		print("Result code: %d" % r.status_code)

def uploadAudio(dictionaryDBFilename, revision, course, debug):
	jar = CookiesJar()
	
	print("Opening dictionaryDB: %s" % dictionaryDBFilename)
	dictionaryDB = DatabaseManager(dictionaryDBFilename)
	
	print("Opening base URL: %s" % (MEMRISE_ENDPOINT + course))
	memrise = requests.get(MEMRISE_ENDPOINT + course, cookies=jar.cookies)
	
	memriseEditURL = memrise.url + "edit"
	print("Opening edit URL: %s" % memriseEditURL)	
	memriseEdit = requests.get(memriseEditURL, cookies=jar.cookies)
	
	soup = BeautifulSoup(memriseEdit.content, 'html.parser')
	
	try:
		levelId = soup.find(attrs={"data-level-id": True}).attrs['data-level-id']
	except:
		passs	
	
	memriseLevelURL = MEMRISE_LEVEL_ENDPOINT + levelId
	
	print("Opening level URL: %s" % memriseLevelURL)		
	
	memriseLevel = requests.get(memriseLevelURL, cookies=jar.cookies)
	
	thingsJson = json.loads(memriseLevel.content)
	
	thingsHtml = re.sub(r'\n', '', thingsJson['rendered'])

	soup = BeautifulSoup(thingsHtml, 'html.parser')
	things = soup.find_all(attrs={"class": "thing"})
	
	total = 0                                                                             
	
	for thing in things:
		soup = BeautifulSoup(str(thing), 'html.parser')
	
		thingId = soup.find(attrs={"class": "thing", "data-thing-id": True }).attrs['data-thing-id']
		
		# Hardocoded column IDs
		# 1 - English word
		# 3 - Audios
		
		word = soup.find(attrs={"data-cell-type": "column", "data-key": "1" }).find(attrs={"class": "text"}).get_text().strip()
		audioCellId = 3
		
		hasAudioFile = soup.find(attrs={"data-cell-type": "column", "data-key": "3" }).find(string=re.compile("no audio file"))
		
		if(hasAudioFile == None):
			continue
		
		print(word)

		audioFilename = getAudioFilename(dictionaryDB, word)
		uploadFileToServer(thingId, audioCellId, memriseEditURL, audioFilename, jar)

		total += 1
		
	print("Total numner: %d" % total)
		
	dictionaryDB.close()	

		
def usage(parser):
	parser.print_help()

def main():
	parser = argparse.ArgumentParser()
	
	parser.add_argument('-dictionaryDB', help="Memrise dictionary db filename (default: memrise.db)", default="memrise.db")
	parser.add_argument('-revision', type=int, help="Revision to output. Not specfied (default): last, 0 - all", default="-1")
	parser.add_argument('-course', help="Memrise course ID", default="1722628")	
	parser.add_argument('-debug', action='store_true', help="Enable debug ", default=False)	
 
	args = parser.parse_args()

	uploadAudio(
		args.dictionaryDB,
		args.revision,
		args.course,
		args.debug
		)
	

if __name__ == "__main__":
    main()
