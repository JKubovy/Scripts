#!/usr/bin/env python3
# Tipsport Playlist Generator
# Version: v0.2.3
'''
 This script generate strm playlist from video-stream of ELH on tipsport.cz
 Example:
	Start stream selector:
		tpg.py > file.strm
	Use specific url:
		tpg.py stream_url > file.strm
'''
# Fill your credentials to tipsport.cz site below
credentials = ('user', 'password')
# Edit programs install paths
# Example:
#	rtmpdump_path = 'C:\\Program Files (x86)\\rtmpdump\\rtmpdump.exe'
#	vlc_path = 'C:\\Program Files (x86)\\VLC\\vlc.exe'
rtmpdump_path = 'rtmpdump'
vlc_path = 'vlc'

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
	parser.add_argument('-v', '--vlc', action='store_true', help='print command to start stream in VLC via rtmpdump')
	parser.add_argument('-c', action='store_true', help='check on GitHub if a new version is available')
	parser.add_argument('-u', action='store_true', help='update/download source code from GitHub')
	global args
	args = parser.parse_args()
def checkUrl():
	'''
	Check if some URL was given as parametr
	If so check URLs category
	If not start Selector
	'''
	if (args.url == ''):
		elh_matches = listELHMatches()
		index = userSelect(elh_matches)
		url = elh_matches[index][3]
		args.url = 'https://www.tipsport.cz/live' + url
	else:
		if (args.url.startswith('www')): 
			args.url = 'https://' + args.url
		if(not checkCategory(args.url)):
			sys.exit()
def eprint(message):
	'''
	Print message to STDERR
	If output stream can't handle UTF-8 characters message will be converted to ASCII
	'''
	try:
		sys.stderr.write(message)
	except UnicodeEncodeError:	
		text = unicodedata.normalize('NFKD', message)
		text = text.encode("utf-8").decode("ascii","ignore")
		sys.stderr.write(text)
	sys.stderr.write('\n')
def generateRandomNumber(lenght):
	'''Generate string with given lenght that contains random numbers'''
	result = ''.join(random.SystemRandom().choice('0123456789') for _ in range(lenght))
	return result
def checkNewVersion(userCall = True):
	'''Check if a new version of this script exist on GitHub'''
	from distutils.version import StrictVersion
	try:
		err = 'Unable to detect current version'
		with open(__file__, 'r') as f:
			currentVersion = StrictVersion(re.search('# ?Version:? ?v?([0-9\.]+)', f.read()).group(1))
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
	'''
	Update this script by downloading source code from GitHub
	credentials, rtmpdump_path and vlc_path variable content will NOT be overwritten
	'''
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
					if (re.match('^credentials', line) is not None):
						f.write(u'credentials = (\'{0}\', \'{1}\')\n'.format(credentials[0], credentials[1]))
					elif (re.match('^rtmpdump_path', line) is not None):
						f.write(u'rtmpdump_path = \'{0}\'\n'.format(rtmpdump_path))
					elif (re.match('^vlc_path', line) is not None):
						f.write(u'vlc_path = \'{0}\'\n'.format(vlc_path))
					else:
						f.write(line + u'\n')
			move(tmpFile, __file__)
			eprint('Script update status: SUCCESS')
		except OSError:
			eprint('Script update status: ERROR')
	else:
		eprint('Script update status: CANCEL')
def login(user, password):
	'''Login to https://www.tipsport.cz site with given credentials and store session'''
	agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36 OPR/42.0.2393.137"
	session.get('https://www.tipsport.cz/')	# load cookies
	payload = {	'agent': agent,
				'requestURI': '/',
				'fPrint': generateRandomNumber(10),
				'userName': user,
				'password': password }
	session.post('https://www.tipsport.cz/LoginAction.do', payload)	# actual login
def checkLogin():
	'''Check if login to https://www.tipsport.cz was successful'''
	page = session.get('https://www.tipsport.cz/')
	if ('LogoutAction.do' in page.text):
		return True
	else:
		return False
def parseStreamDWRresponse(responseText):
	'''
	Parse response and try to get stream metadata
	Expect <smil>...</smil> format of response
	'''
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
def getToken(page):
	'''Get scriptSessionId from page for proper DWRScript call'''
	token = re.search('JAWR.dwr_scriptSessionId=\'([0-9A-Z]+)\'', page)
	if(token == None):
		eprint('Unable to detect scriptSessionId')
		sys.exit()
	token = token.group(1)
	return token
def getStreamNumber(url):
	'''
	Parse stream number from URL
	Example:
		https://www.tipsport.cz/live/basketbal-unics-kazan-aefes/2533087 -> 2533087
	'''
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
def userSelect(matches, index_name = 0):
	'''
	Start selector that allow user to choose stream from list
	matches is two-dimensional array
	index_name is index to array where the name of match is stored
	'''
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
def listELHMatches():
	'''Get list of all available ELH streams on https://www.tipsport.cz/tv'''
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
	return elh_matches
def checkCategory(url):
	'''Check if the url point to ELH stream'''
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
	'''Print generated content of strm file'''
	swf = 'https://www.tipsport.org/scripts/libs/flowplayer/flowplayer.swf'
	flashVer = 'WIN\\2024,0,0,194'
	print('{0} playpath={1} app={2} pageURL={3} flashVer={7} swfUrl={4} live={5} swfVfy={6}'.format(rtmp, playpath, app, pageURL, swf, live, swfVfy, flashVer))
def printVLC(url, playpath, app, pageURL):
	'''Print command to start stream in vlc via rtmpdump'''
	swf = 'https://www.tipsport.org/scripts/libs/flowplayer/flowplayer.swf'
	flashVer = 'WIN 24,0,0,194'
	print('{6} -r "{0}" -y "{1}" -a "{2}" -p "{3}" -W "{4}" -f "{5}" --live -q | {7} -q -'.format(url, playpath, app, pageURL, swf, flashVer, rtmpdump_path, vlc_path))
def main():
	parseArgs()
	if (args.c and not args.u):
		checkNewVersion()
		return
	if (args.u):
		updateCode()
		return
	checkUrl()
	user,password = credentials
	login(user, password)
	if (checkLogin()):
		(rtmp, playpath, app) = getStreamMetadata(args.url)
		if (args.vlc): 
			printVLC(rtmp, playpath, app, args.url)
			eprint('Command successful generated')
		else: 
			printPlaylist(rtmp, playpath, app, args.url)
			eprint('Playlist successful generated')
	else:
		eprint('Login to Tipsport.cz fails\nCheck credentials or internet connection')

if __name__ == "__main__":
	main()