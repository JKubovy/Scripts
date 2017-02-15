#!/usr/bin/env python3
# Tipsport Playlist Generator
# This script generate strm playlist from video-stream of ELH on tipsport.cz
# Using	Linux:	tpg.py stream url > file.strm
#
# Fill your credentials to tipsport.cz site below
credentials = ('user', 'password')

import re
import sys
import random
import requests

session = None

# print to stderr
def eprint(message):
    sys.stderr.write(message)
# Generate string with 10 random digits
def generatefPrint(lenght):
	result = ''.join(random.SystemRandom().choice('0123456789') for _ in range(lenght))
	return result
# Login to tvtipsport.cz site and store session
def login(user, password):
	global session
	agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36 OPR/42.0.2393.137"
	session = requests.session()
	session.get('https://www.tipsport.cz/')	# load cookies
	payload = {	'agent': agent,
				'requestURI': '/',
				'fPrint': generatefPrint(10),
				'userName': user,
				'password': password }
	session.post('https://www.tipsport.cz/LoginAction.do', payload)	# actual login
# Check if login to site was successful
def checkLogin():
	page = session.get('https://www.tipsport.cz/')
	if ('LogoutAction.do' in page.text):
		return True
	else:
		return False
def parseStreamDWRresponse(responseText):
	url = re.search('meta base\=\"(.*)\"', responseText)
	if (not url.group(1)):
		eprint('Unable parse stream metadata: url')
		sys.exit()
	url = url.group(1)
	playpath = re.search('video src\=\"(.*?)\"', responseText)
	if (not playpath.group(1)):
		eprint('Unable parse stream metadata: playpath')
		sys.exit()
	playpath = playpath.group(1)
	app = url.split(':80/')[-1]
	return (url, playpath, app)
# Get scriptSessionId from page for proper DWRScript call
def getToken(page):
	token = re.search('JAWR.dwr_scriptSessionId=\'([0-9A-Z]+)\'', page)
	if(not token.group(1)):
		eprint('Unable to detect scriptSessionId')
		sys.exit()
	token = token.group(1)
	return token
def getStreamNumber(url):
	relativeURL = url.replace('https://www.tipsport.cz', '')
	tokens = (relativeURL.split('/'))
	number = list(filter(None, tokens))[-1]
	try:
		int(number)
	except ValueError:
		eprint('Unable to get StreamNumber')
		sys.exit()
	return number
def getStreamMetadata(url):
	page = session.get(url)
	token = getToken(page.text)
	relativeURL = url.replace('https://www.tipsport.cz', '')
	DWRScript = 'https://www.tipsport.cz/dwr/call/plaincall/StreamDWR.getStream.dwr'
	number = 'number:' + getStreamNumber(url)
	payload={	'callCount': 1,
				'page': relativeURL,
				'httpSessionId': '',
				'scriptSessionId': token,
				'c0-scriptName': 'StreamDWR',
				'c0-methodName': 'getStream',
				'c0-id': 0,
				'c0-param0': number,
				'c0-param1': 'string:SMIL',
				'batchId': 9}
	response = session.post(DWRScript, payload)
	pattern = '\"(.*)\"'
	responseUrl = re.search(pattern, response.text)
	if (responseUrl == None):	# use 'string:RTMP' insted of 'string:SMIL'
		payload['c0-param1'] = 'string:RTMP'
		response = session.post(DWRScript, payload)
	responseUrl = re.search(pattern, response.text)
	if (responseUrl == None):	# StreamDWR.getStream.dwr not working on this specific stream
		eprint('Can\'t get stream metadata')
		sys.exit()	
	url = responseUrl.group(1)
	response = session.get(url)
	return parseStreamDWRresponse(response.text)
# Check if the url point to ELH stream
def checkCategory(url):
	page = session.get(url)
	token = getToken(page.text)
	relativeURL = url.replace('https://www.tipsport.cz', '')
	DWRScript = 'https://www.tipsport.cz/dwr/call/plaincall/Multiple.2.dwr'
	number = 'number:' + getStreamNumber(url)
	payload={	'callCount': 2,
				'page': relativeURL,
				'httpSessionId': '',
				'scriptSessionId': token,
				'c0-scriptName': 'LiveOdds2DWR',
				'c0-methodName': 'getMatch',
				'c0-id': 0,
				'c0-param0': number,
				'c1-scriptName': 'LiveTicketDWR',
				'c1-methodName': 'updateTicket',
				'c1-id': 1,
				'c1-param0': 'string:100',
				'c1-param1': 'string:ALL',
				'batchId': 4}
	response = session.post(DWRScript, payload)
	competition = re.search('s0\.competition\=\"(.*?)\"', response.text)
	if (not competition.group(1)):
		eprint('Unable detect competition')
		return False
	competition = competition.group(1)
	if (competition in ['Tipsport extraliga', 'CZ Tipsport extraliga']):
		return True
	else:
		eprint('Stream is not ELH')
		return False
def parseArgs():
	if (len(sys.argv) == 1):
		eprint('No url given')
		sys.exit()
	else:
		url = sys.argv[-1]
		if (url.startswith('www')): 
			url = 'https://' + url
		return url
def printPlaylist(rtmp, playpath, app, pageURL, live='true', swfVfy='true'):	# TODO ? remove swfVfy and fleshVer
	swf = 'https://www.tipsport.org/scripts/libs/flowplayer/flowplayer.swf'
	flashVer = 'WIN\\2024,0,0,194'
	print('{0} playpath={1} app={2} pageURL={3} flashVer={7} swfUrl={4} live={5} swfVfy={6}'.format(rtmp, playpath, app, pageURL, swf, live, swfVfy, flashVer))
def main():
	user,password = credentials
	login(user, password)
	if (checkLogin()):
		url = parseArgs()
		if (checkCategory(url)):
			(rtmp, playpath, app) = getStreamMetadata(url)
			printPlaylist(rtmp, playpath, app, url)
			eprint('Playlist successful generated')
	else:
		eprint('Login to Tipsport.cz fails\ncheck credentials or internet connection')

if __name__ == "__main__":
	main()