# kindle-to-memrise

## Introduction

A script to pull Kindle Vocabulary Builder DB and convert into Memrise course (`kindle2memrise.py`)

Another script (`uploadAudio.py`) can upload audio mp3s to the course.

The latest Kindle Paperwhite (second generation) offers the Vocabulary Builder feature. With Vocabulary Builder, you can look up words with the dictionary and memorize their definitions.

For my self-education I use [http://memrise.com/](http://memrise.com/) (both on my phone and desktop PC). I thought it would be great to pull words which I've checkded when reading English books on my Kindle and push them into my Memrise course.

## How does it work?

### Create course (`kindle2memrise.py`)

1. The script reads through the vocab.db to look for all Engligh words (in table WORDS).
2. Each of the words (aka _stems_) is used for a definition lookup in the [Cambridge Dictionary](https://dictionary.cambridge.org/)
3. Retreve word definitions, usage example, pronounciation, audio mp3 and insert into a new SQLite database `memrise.db` (the mp3 is written to the disk only, folder `audio`) 
4. Each new word is written to a text file, in a format suitable for bulk words import into Memrise.

### Upload audio files (`uploadAudio.py`)

1. Get list of all words from the course
2. If a word still does not have any audio file...
3. ...retireves mp3 filename from the DB created in the 1st stage
4. Uploads the mp3 to Memrise

## Pre-requisties

* Kindle Paperwhite (or newer)
* `vocab.db` file (retrieved from your Kindle, from `/Volumes/Kindle/system/vocabulary/`)
* python 3
* BeautifulSoup
* requests

## References

I heavily sourced from two GitHub projects:

* [cambridge-cli](https://github.com/pasternak/cambridge-cli)
* [bulk-audio-upload](https://github.com/DrewSSP/bulk-audio-upload)

Also, I was using these documents and toold:

* [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* [requests](http://requests.readthedocs.io/en/master/user/quickstart/)
* [Edit This Cookie!](https://chrome.google.com/webstore/detail/editthiscookie/)

And finally, my webpage:

* [http://jhartman.pl](http://jhartman.pl/2017/11/05/kindle-vocabulary-builder-into-memrise/)


## ToDOs

* Parametrize hardcoded things - especially language pair English-Polish
* Upload Audio files with prononciation 

# Usage `kindle2memrise.py`

## DB conversion

```
MBP:kindle-to-memrise jhartman$ ./kindle2memrise.py -h
usage: kindle2memrise.py [-h] [-kindleDB KINDLEDB]
                         [-dictionaryDB DICTIONARYDB] [-output OUTPUT]
                         [-revision REVISION] [-debug]

optional arguments:
  -h, --help            show this help message and exit
  -kindleDB KINDLEDB    Kindle vocabulary db filename (default: vocab.db)
  -dictionaryDB DICTIONARYDB
                        Memrise dictionary db filename (default: memrise.db)
  -output OUTPUT        Output file to import to memrise.com (default:
                        memrise.txt)
  -revision REVISION    Revision to output. Not specfied (default): last, 0 -
                        all
  -debug                Enable debug
```
  
At minimum, the tool does not require any parameters, it will search for `vocab.db` in the current folder and will write output files into the same, current folder.

Pay your special attention to `memrise.txt` which has been generated:

```
MBP:kindle-to-memrise jhartman$ tail memrise.txt
mere	Sam. Used to emphasize that something is not large or important. Example: It costs a mere twenty dollars.	mɪər
thinning	Rozcieńczać, rozrzedzać. To make a substance less thick, often by adding a liquid to it. Example: N/A	θɪn
carnivore	Zwierzę mięsożerne. An animal that eats meat. Example: N/A	ˈkɑːnɪvɔːr
embrace	Obejmować (się). If you embrace someone, you put your arms around them, and if two people embrace, they put their arms around each other.. Example: We are always eager to embrace the latest technology.	ɪmˈbreɪs
```
This is the file, which will be used for [bulk word add](http://feedback.memrise.com/knowledgebase/articles/525095-add-words-to-my-course-or-upload-words-from-a-spre) into your Course.

## Bulk word add

Create a new Course.

In the course, add two new columns: **Definition** and **Example**.

Edit settings for both of new columns, edit attributes:

* *Definition* - edit settings:
	* *Display* - only _Show after tests_ is selected 
	* *Testing* - all options unselected
* *Example* - edit settings:
	* *Display* - all options unselected
	* *Testing* - only _Tapping Tests Enabled_ is selected 

Go to your Course, press Edit and in the Advanced options, look for _Bulk add words_:

![Bulk Add words](http://jhartman.pl/files/memrise/01%20-%20memrise.png)

Open `memrise.txt` in an editor (e.g. Notepad), select all, copy it and paste into Memrise Bulk Add form then press _Add_:

![Bulk Add words](http://jhartman.pl/files/memrise/02%20-%20memrise.png)

# Usage `uploadAudio.py`

```
usage: uploadAudio.py [-h] [-dictionaryDB DICTIONARYDB] [-revision REVISION]
                      [-course COURSE] [-debug]

optional arguments:
  -h, --help            show this help message and exit
  -dictionaryDB DICTIONARYDB
                        Memrise dictionary db filename (default: memrise.db)
  -revision REVISION    Revision to output. Not specfied (default): last, 0 -
                        all
  -course COURSE        Memrise course ID
  -debug                Enable debug
```

1. Login to the memrise and export cookies (using Chrome [Edit This Cookie!](https://chrome.google.com/webstore/detail/editthiscookie/) extension)
2. TBD

# Support

Your support on Buy Me a Coffee is invaluable, motivating me to continue crafting bytes that matters – thank you sincerely 👍

<a href="https://www.buymeacoffee.com/jhartman" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>


  
  
