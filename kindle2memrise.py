#!/usr/bin/env python3

import os
import re
import sys
import argparse
import sqlite3

from urllib.request import urlopen
from urllib.request import urlretrieve

from bs4 import BeautifulSoup


CAMBRIDGE_ENDPOINT = \
    "https://dictionary.cambridge.org/search/english-polish/direct/?q="
    
# https://github.com/pasternak/cambridge-cli/blob/master/cambridge-cli.py
# https://github.com/DrewSSP/bulk-audio-upload

class Translation(object):
	def translate(self):
		term = re.sub(r"\s", "-", self.word)
		
		try:
			cdict = urlopen(CAMBRIDGE_ENDPOINT + term)
			if (cdict.getcode() != 200):
				print("Error")
				return
		except:
			return
			
		soup = BeautifulSoup(cdict, 'html.parser')
		
		desc = definition = example = pronunciation = audiofileURL = None			
			
		try:
			translation = soup.find(attrs={"class": "trans"}).get_text().strip()
		except:
			translation = None
			
		try:
			definition = soup.find(attrs={"class": "def"}).get_text().strip().capitalize()
		except:
			definition = None
			
		try:
			example = soup.find(attrs={"title": "Example"}).get_text().strip()
		except:
			example = None
			
		try:
			pronunciation = soup.find(attrs={"class": "ipa"}).get_text().strip()
		except:
			pronunciation = None
			
		try:
			audiofileURL = soup.find(attrs={"data-src-mp3": True}).attrs['data-src-mp3']
		except:
			audiofileURL = None	
		
		if(translation == None):
			translation = definition
			definition = None
			
		print("\n\033[1m%s:\033[0m" % term)
		print("\t>> %s" % translation )
		
		print("\n[-] Definition:")
		print("\t%s\n" % definition)

		print("\n[-] Example:")
		print("\t%s\n" % example)

		print("\n[-] Pronunciation:")
		print("\t%s\n" % pronunciation)
		
		print("\n[-] Audio URL:")
		print("\t%s\n" % audiofileURL)
		
		self.translation = translation
		
		self.definition = definition
		self.example = example
		
		self.pronunciation = pronunciation
		self.audiofileURL = audiofileURL
		
		self.audiofilePath = downloadAudioFile(audiofileURL, term)

	def __init__(self, word):
		self.word = word
		self.translation = None
		self.definition = None		
		self.pronunciation = None
		self.partofdpeech = None
		self.gender = None
		self.audiofileURL = None
		self.audiofilePath = None
		
		self.translate()
		

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

def translate(kindleDBFilename, dictionaryDBFilename, outputFilename, outputRevision, debug):
	newWords = 0
	
	print("Opening kindleDB: %s" % kindleDBFilename)
	kindleDB = DatabaseManager(kindleDBFilename)
	
	print("Opening dictionaryDB: %s" % dictionaryDBFilename)
	dictionaryDB = DatabaseManager(dictionaryDBFilename)
	
	
	dictionaryDB.query("CREATE TABLE IF NOT EXISTS dictionary (word TEXT UNIQUE, translation TEXT, definition TEXT, example TEXT, pronunciation TEXT, partofdpeech TEXT, gender TEXT, audiofileURL TEXT, audiofilePath TEXT, revision INTEGER)")
	
	try:
		revisions = dictionaryDB.query("SELECT MAX(revision) FROM dictionary")
		revision = revisions.fetchone()[0] + 1
	except:
		revision = 1
	
	rows = kindleDB.query("SELECT stem FROM WORDS WHERE lang='en'")
	
	while True:
		row = rows.fetchone()
			
		if row == None:
			break
	
		# stem (i.e. word)
		word = row[0]; 
		
		if(debug):
			print("Found in KindleDB: %s" % word)
		
		alreadyInDB = dictionaryDB.query("SELECT COUNT(*) FROM dictionary where word=?", [word])
		
		if(alreadyInDB.fetchone()[0] > 0):
			continue;
		
		try:
			
			translated = Translation(word)
			
			dictionaryDB.query("INSERT INTO dictionary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
			[
				translated.word, 
				translated.translation,
				translated.definition,
				translated.example,				
				translated.pronunciation,
				translated.partofdpeech,
				translated.gender,
				translated.audiofileURL,
				translated.audiofilePath,
				revision
			] )

			if(translated.translation != None):
				newWords += 1
		except sqlite3.Error as e:
				print("Skipping.... %s" % e)
				
	# If no new words, fallback to the previous revision)
	
	print("Number of new words: %d" % newWords)
	
	#if(newWords == 0):
	#	revision -= 1
		
	if(outputRevision == 0):
		print
		revision = 0

	outputMemrise(dictionaryDB, revision, outputFilename)
	
	# dictionaryDB.query("DELETE FROM dictionary WHERE word=?", [ "retorted" ]);

	dictionaryDB.close()
	kindleDB.close()

def outputMemrise(dictionaryDB, revision, outputFilename):
	print ("Writting output memrise file: %s" % outputFilename)
	print ("Revision (or greater) %d " % revision)
	
	try:
		with open(outputFilename, 'w') as f:
			cursor = dictionaryDB.query("SELECT word, translation, definition, example, pronunciation, partofdpeech, gender FROM  dictionary WHERE definition IS NOT NULL AND revision >= ?", [revision])
			
			while True:
				row = cursor.fetchone()
				
				if(row == None):
					break
				
				outputLine = ""
				
				for i in row:
					if(i == None):
						outputLine += "\t"
					else:
						outputLine += i + "\t"
					
				print(outputLine, file=f)
	except Error as e:
		print ("Error writting the file" + e)
		
def downloadAudioFile(URL, filename):
	directory = 'audio'
	
	filename = filename.replace(" ", "_")

	if not os.path.exists(directory):
		os.makedirs(directory)
		
	try:
		filename = os.path.join(directory, filename + '.mp3')
		urlretrieve(URL, filename)
	except:
		filename = None
		
	return filename
		
def usage(parser):
	parser.print_help()

def main():
	parser = argparse.ArgumentParser()
	
	parser.add_argument('-kindleDB', help="Kindle vocabulary db filename (default: vocab.db)", default="vocab.db")
	parser.add_argument('-dictionaryDB', help="Memrise dictionary db filename (default: memrise.db)", default="memrise.db")
	parser.add_argument('-output', help="Output file to import to memrise.com (default: memrise.txt)", default="memrise.txt")	
	parser.add_argument('-revision', type=int, help="Revision to output. Not specfied (default): last, 0 - all", default="-1")
	parser.add_argument('-debug', action='store_true', help="Enable debug", default=False)	
 
	args = parser.parse_args()

	translate(
		args.kindleDB, 
		args.dictionaryDB,
		args.output,
		args.revision,
		args.debug
		)


if __name__ == "__main__":
    main()
