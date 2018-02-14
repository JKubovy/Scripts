#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

__author__ = "Jan Kubovy"
__email__ = "JanKubovy94@gmail.com"


'''
Script renaming subtitles to match movie and tv show name.
Try to find all video and subtitle files in given folder and match them.
For comparing names using module guessit.
'''

import logging, os
from glob import iglob
from argparse import ArgumentParser
from guessit import guessit

default_video_extensions = ['mkv', 'mp4', 'm4v', 'avi']
default_subtitle_extensions = ['srt', 'sub']
logger = logging.getLogger(__name__)

def get_arguments():
	'''Process script arguments'''
	parser = ArgumentParser(description=__doc__)
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-v', '--verbose', help='verbose (debug) logging',
					   action='store_const', const=logging.DEBUG, dest='loglevel')
	group.add_argument('-q', '--quiet', help='silent mode, only log warnings',
					   action='store_const', const=logging.WARN, dest='loglevel')
	parser.add_argument('-r', '--recursive', help='rename files recursively in subfolders', action='store_true')
	parser.add_argument('--video_extensions', help='video extensins', nargs='*', metavar='.ext', default=default_video_extensions)
	parser.add_argument('--subtitle_extensions', help='subtitles extensins', nargs='*', metavar='.ext', default=default_subtitle_extensions)
	parser.add_argument('--dry_run', help='no file will be renamed', action='store_true')
	parser.add_argument('--rename_video', help='rename video files insted of subtitle', action='store_true')
	parser.add_argument('-m', '--movies', help='process movies', action='store_true')
	parser.add_argument('-s', '--shows', help='process tv shows', action='store_true')
	parser.add_argument('dir', help='start directories (default=\'.\')', nargs='*', default='.')
	args = parser.parse_args()
	return check_arguments(args)

def check_arguments(args):
	'''Correct arguments and set some default values base on multiple arguments'''
	for i in range(len(args.dir)):
		if args.dir[i].endswith('"'): # Windows path ends with \. That cause wrong parsing and it has to be checked
			args.dir[i] = args.dir[i][:-1] + '\\'
	if not args.movies and not args.shows:
		args.movies = True
		args.shows = True
	if not args.loglevel:
		args.loglevel = logging.INFO
	return args
	
def init_logger(loglevel):
	'''Create console logger and store it in 'logger' variable'''
	logger.setLevel(logging.DEBUG)
	handler = logging.StreamHandler()
	handler.setLevel(loglevel)
	handler.setFormatter(logging.Formatter('%(levelname)s\t%(message)s'))
	logger.addHandler(handler)
	
class Renamer:
	'''Worker that finding and renaming subtitles'''
	def __init__(self, args):
		'''Store arguments and init counter'''
		self.args = args
		self.count_renamed = 0
		self.count_skipped = 0
		self.count_no_subtitles = 0
	
	def next_directory(self):
		'''Expanding given directories and yield them'''
		for start_directory in args.dir:
			for possible_directory in iglob(start_directory):
				if os.path.isdir(possible_directory):
					yield possible_directory
	
	def start(self):
		'''Start finding video and subtitle files and rename them'''
		for start_directory in self.next_directory():
			for root, _, files in os.walk(start_directory):
				logger.debug('Entering folder: {0}'.format(root))
				movies, tvshows, subtitles = self.get_videos_and_subtitles(files)
				if args.movies:
					self.find_sub_for_movies(root, movies, subtitles)
				if args.shows:
					self.find_sub_for_shows(root, tvshows, subtitles)
				if not self.args.recursive:
					break
		self.print_info()
	
	def check_subtitles(self, root, video, possible_subtitles):
		'''Check if it was founded suitable subtitles and if there is just one. If so call try_rename_subtitles method'''
		if len(possible_subtitles) == 0:
			self.count_no_subtitles += 1
			logger.info('No subtitle: {0}'.format(video['orig_name']))
		elif len(possible_subtitles) == 1:
			if not self.args.rename_video:
				self.try_rename_subtitles(root, video['orig_name'], possible_subtitles[0]['orig_name'])
			else:
				self.try_rename_subtitles(root, possible_subtitles[0]['orig_name'], video['orig_name'])
		else:
			logger.warning('More then one suitable subtitles: {0}'.format(video['orig_name']))
	
	def find_sub_for_movies(self, root, movies, subtitles):
		'''Try to find suitable subtitle for every movie in movies collection'''
		for movie in movies:
			if 'title' in movie:
				possible_subtitles = [sub for sub in subtitles if ('title' in sub and sub['title'] == movie['title'])]
				self.check_subtitles(root, movie, possible_subtitles)
			else:
				logger.debug('Unrecognized movie name: {0}'.format(movie['orig_name']))
	
	def find_sub_for_shows(self, root, shows, subtitles):
		'''Try to find suitable subtitle for every tv show in shows collection'''
		for show in shows:
			if all(item in show for item in ['title', 'season', 'episode']):
				possible_subtitles = [sub for sub in subtitles if (all(item in sub for item in ['title', 'season', 'episode']) and sub['title'] == show['title'] and sub['season'] == show['season'] and show['episode'] == sub['episode'])]
				self.check_subtitles(root, show, possible_subtitles)
			else:
				logger.debug('Unrecognized TV show metadata: {0}'.format(show['orig_name']))
	
	def try_rename_subtitles(self, root, source_filename, to_rename_filename):
		'''Check if the subtitle name match video neame and if not rename subtitle file'''
		source_name, source_extension = os.path.splitext(source_filename)
		to_rename_name, to_rename_extension = os.path.splitext(to_rename_filename)
		if source_name == to_rename_name:
			logger.debug('Skipped (already named right): {0}'. format(source_name))
			self.count_skipped += 1
		else:
			logger.info('Renamed: {0} -> {1}'.format(to_rename_filename, source_name + to_rename_extension))
			if not args.dry_run:
				os.rename(os.path.join(root, to_rename_name + to_rename_extension), os.path.join(root, source_name + to_rename_extension))
			self.count_renamed += 1
	
	def get_videos_and_subtitles(self, files):
		'''Split given files into three collections. Return movies, tv shows and subtitles'''
		movies = []
		tvshows = []
		subtitles = []
		for filename in files:
			if not any(filename.endswith(ext) for ext in self.args.video_extensions + self.args.subtitle_extensions): # drop unwanted files
				continue
			logger.debug('Parsing name: {0}'.format(filename))
			try:
				name_parsed = guessit(filename.replace('-', '_').lower())
				name_parsed['orig_name'] = filename
				if name_parsed['container'] in self.args.video_extensions:
					if name_parsed['type'] == 'movie':
						movies.append(name_parsed)
					elif name_parsed['type'] == 'episode':
						tvshows.append(name_parsed)
				elif name_parsed['container'] in self.args.subtitle_extensions:
					subtitles.append(name_parsed)
			except KeyError:
				logger.debug('Unrecognized: {0}'.format(filename))
		return movies, tvshows, subtitles
	
	def print_info(self):
		'''Print how many files were processed'''
		if self.count_renamed > 0:
			logger.info('Renamed files: {0}'.format(self.count_renamed))
		if self.count_skipped > 0:
			logger.info('Skipped files: {0}'.format(self.count_skipped))
		if self.count_no_subtitles > 0:
			logger.info('No subtitles: {0}'.format(self.count_no_subtitles))	
				
def main(args):
	init_logger(args.loglevel)
	logger.debug('Arguments: {0}'.format(vars(args)))
	renamer = Renamer(args)
	renamer.start()


if __name__ == '__main__':
	try:
		args = get_arguments()
		main(args)
	except KeyboardInterrupt:
		pass
