#!/usr/bin/env python3
# Hokejka Playlist Generator
# This script generate strm playlist from video-stream of ELH on hokej.cz/hokejka/tv
# Using:	hpg.py > file.strm	

import re
import sys
import json
import random
import requests
from datetime import date

session = requests.session()

# Print to stderr
def eprint(message):
	sys.stderr.write(message)
	sys.stderr.write('\n')
def printPlaylist(rtmp, playpath, app, live='true'):
	print('{0} playpath={1} app={2} live={3}'.format(rtmp, playpath, app, live))
# Parse response and dig stream metadata
def parseSMILresponse(responseText):
	if ('<smil>' in responseText):
		try:
			url = (re.search('meta base\=\"(.*?)\"', responseText)).group(1)
			playpath = (re.search('video src\=\"(.*?)\"', responseText)).group(1)
			app = (url.split(':80/'))[1]
		except (AttributeError, IndexError):
			eprint('Unable to parse stream metadata')
			sys.exit()
	else:
		eprint('Unsupported format of stream metadata')
		sys.exit()
	return (url, playpath, app)
# Let the user choose stream from list
def userSelect(matches, index_name = 0):
	for i in range(len(matches)):
		eprint('{0}\t{1}'.format(i+1, matches[i][index_name]))
	found = False
	while (not found):
		eprint('Select one of stream by writing number {0}-{1}'.format(1, len(matches)))
		i = input()
		try:
			number = int(i)
		except ValueError:
			eprint('Please write number')
			continue
		if (not number in range(1, len(matches) + 1)):
			eprint('Wrong stream index')
		else:
			eprint('Chosen stream: {0}'.format(matches[number-1][index_name]))
			found = True
	return(number-1)
# Get all available ELH stream on hokej.cz/hokejka/tv and call userSelect()
# return: stadion where is the match
def listMatches():
	today = date.today()
	url = 'http://hokej.cz.s3.amazonaws.com/scoreboard/{0}-{1:02}-{2:02}.json'.format(today.year, today.month, today.day)
	response = session.get(url)
	try:
		data = json.loads(response.text)
		matches = data['57']['matches']
		list = []
		for match in matches:
			list.append(['{0} - {1}'.format(match['home']['short_name'], match['visitor']['short_name']), match['home']['shortcut'].lower()])
		index = userSelect(list)
		stadion = list[index][1]
	except (KeyError, IndexError, ValueError):
		eprint('No ELH stream found')
		sys.exit()
	return(stadion)
def getStreamMetadata(stadion):
	response = session.get('http://api.elh.livebox.cz/v1/embed-delayed.js')
	urls = re.findall('\"([a-z]+?)\"\:\{\"rtmp_smil\"\:\"(.*?)\"',response.content.decode('unicode-escape'))
	matches = [(s,m) for (s,m) in urls if s == stadion]
	if (len(matches) == 0):
		eprint('Unable to find stream')
		sys.exit()
	url = matches[0][1].replace('\\','')
	response = session.get(url)
	return parseSMILresponse(response.text)
def main():
	session.headers.update({'Referer': 'http://www.hokej.cz/hokejka/tv'})
	stadion = listMatches()
	(rtmp, playpath, app) = getStreamMetadata(stadion)
	printPlaylist(rtmp, playpath, app)
	eprint('Playlist successful generated')
		
if __name__ == "__main__":
	main()