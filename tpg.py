#!/usr/bin/env python3
# Tipsport Playlist Generator
# Version: v0.2
# This script generate strm playlist from video-stream of ELH on tipsport.cz
# Using:
#	Start stream selector:		tpg.py > file.strm	
#	Use specific url:		tpg.py stream_url > file.strm
#
# Fill your credentials to tipsport.cz site below
credentials = ('user', 'password')

import re
import sys
import random
import requests
import argparse
import unicodedata

session = requests.session()
args = None
githubUrl = 'https://raw.githubusercontent.com/Xsichtik/Scripts/master/tpg.py'

def parseArgs():
	parser = argparse.ArgumentParser(description='Script that generate strm playlist of ELH stream on tipsport.cz')
	parser.add_argument('url', nargs='?', default='', help='URL of ELH stream on tipsport.cz')
	parser.add_argument('-c', action='store_true', help='check on GitHub if a new version is available')
	parser.add_argument('-u', action='store_true', help='update/download source code from GitHub')
	global args
	args = parser.parse_args()
def checkUrl():
	if (args.url == ''):
		args.url = listMatches()
	else:
		if (args.url.startswith('www')): 
			args.url = 'https://' + args.url
		if(not checkCategory(args.url)):
			sys.exit()
# print to stderr
def eprint(message):
	try:
		sys.stderr.write(message)
	except UnicodeEncodeError:	
		text = unicodedata.normalize('NFKD', message)
		text = text.encode("utf-8").decode("ascii","ignore")
		sys.stderr.write(text)
	sys.stderr.write('\n')
# Generate string with 10 random digits
def generateRandomNumber(lenght):
	result = ''.join(random.SystemRandom().choice('0123456789') for _ in range(lenght))
	return result
def checkNewVersion(userCall = True):
	from distutils.version import StrictVersion
	try:
		err = 'Unable to detect current version'
		with open(__file__, 'r') as f:
			currentVersion = StrictVersion(re.search('# Version: v([0-9\.]+)', f.read()).group(1))
		err = 'Unable to detect new version'
		newCode = requests.get(githubUrl).text
		newVersion = StrictVersion(re.search('# Version: v([0-9\.]+)', newCode).group(1))
	except AttributeError:
		eprint(err)
		return False
	if (currentVersion < newVersion):
		eprint('New version is available')
		if(userCall): eprint('Run script with -u parametr for update')
		return True
	else:
		eprint('You already have newest version')
		return False
def updateCode():
	eprint('Script update status: CHECKING')
	newVersion = checkNewVersion(False)
	if (not newVersion): return
	import os
	from shutil import move
	eprint('Are you sure you want to UPDATE script (y/n)?')
	i = input()
	if (i in ['y', 'Y']):
		try:
			newCode = requests.get(githubUrl)
			tmpFile = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + '_tpg.tmp'
			with open(tmpFile, 'w', encoding='utf-8') as f:
				for line in newCode.text.split('\n'):
					if(re.match('^credentials ?\= ?\(.*\)', line) is not None):
						f.write(u'credentials = (\'{0}\', \'{1}\')\n'.format(credentials[0], credentials[1]))
					else:
						f.write(line + u'\n')
			move(tmpFile, __file__)
			eprint('Script update status: SUCCESS')
		except OSError:
			eprint('Script update status: ERROR')
	else:
		eprint('Script update status: CANCEL')
# Login to tvtipsport.cz site and store session
def login(user, password):
	agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36 OPR/42.0.2393.137"
	session.get('https://www.tipsport.cz/')	# load cookies
	payload = {	'agent': agent,
				'requestURI': '/',
				'fPrint': generateRandomNumber(10),
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
# Parse response and dig stream metadata
def parseStreamDWRresponse(responseText):
	# Expect <smil>...</smil> format of response
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
# Get scriptSessionId from page for proper DWRScript call
def getToken(page):
	token = re.search('JAWR.dwr_scriptSessionId=\'([0-9A-Z]+)\'', page)
	if(token == None):
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
# Let the user choose stream from list
def userSelect(matches, index_name = 0):
	for i in range(len(matches)):
		eprint(u'{0}\t{1}'.format(i+1, matches[i][index_name]))
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
			eprint(u'Chosen stream: {0}'.format(matches[number-1][index_name]))
			found = True
	return(number-1)
# Get list of all streams on tipsport.cz and call userSelect()
def listMatches():
	page = session.get('https://www.tipsport.cz/tv')
	token = getToken(page.text)
	DWRScript = 'https://www.tipsport.cz/dwr/call/plaincall/LiveOdds2DWR.getMatchesBothMenu.dwr'
	payload={	'callCount': 1,
				'page': '/tv',
				'httpSessionId': '',
				'scriptSessionId': token,
				'c0-scriptName': 'LiveOdds2DWR',
				'c0-methodName': 'getMatchesBothMenu',
				'c0-id': 0,
				'c0-param0': 'number:0',
				'c0-param1': 'number:0',
				'c0-param2': 'boolean:true',
				'c0-param3': 'string:COMPETITION_SPORT',
				'batchId': 2}
	response = session.post(DWRScript, payload)
	response.encoding = 'utf-8'
	matches = re.findall('.*abbreaviation=\"(.*?)\".*competition=\"(.*?)\".*sport=\"(.*?)\".*url=\"(.*?)\".*', response.content.decode('unicode-escape'))
	elh_matches = []
	for m in matches:
		if (m[1] in ['Tipsport extraliga', 'CZ Tipsport extraliga']):
			elh_matches.append(m)
	if (len(elh_matches) == 0):
		eprint('No ELH stream found')
		sys.exit()
	index = userSelect(elh_matches)
	url = elh_matches[index][3]
	return('https://www.tipsport.cz/live' + url)
# Check if the url point to ELH stream
def checkCategory(url):
	try:
		page = session.get(url)
	except requests.exceptions.RequestException:
		eprint('Bad url given')
		sys.exit()
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
	if (competition == None):
		eprint('Unable to detect competition')
		return False
	competition = competition.group(1)
	if (competition in ['Tipsport extraliga', 'CZ Tipsport extraliga']):
		return True
	else:
		eprint('Stream is not ELH')
		return False
def printPlaylist(rtmp, playpath, app, pageURL, live='true', swfVfy='true'):
	swf = 'https://www.tipsport.org/scripts/libs/flowplayer/flowplayer.swf'
	flashVer = 'WIN\\2024,0,0,194'
	print('{0} playpath={1} app={2} pageURL={3} flashVer={7} swfUrl={4} live={5} swfVfy={6}'.format(rtmp, playpath, app, pageURL, swf, live, swfVfy, flashVer))
def main():
	user,password = credentials
	parseArgs()
	if (args.c and not args.u):
		checkNewVersion()
		return
	if (args.u):
		updateCode()
		return
	checkUrl()
	login(user, password)
	if (checkLogin()):
		(rtmp, playpath, app) = getStreamMetadata(args.url)
		printPlaylist(rtmp, playpath, app, args.url)
		eprint('Playlist successful generated')
	else:
		eprint('Login to Tipsport.cz fails\ncheck credentials or internet connection')

if __name__ == "__main__":
	main()