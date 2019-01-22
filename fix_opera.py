#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Jan Kubovy"
__email__ = "JanKubovy94@gmail.com"

'''
Script removes default search engine from Opera so you can set any search shortcut in Opera browser.
You need to run it as Administrator
'''

import os
import stat
import glob
import shutil

FILENAME = 'default_partner_content.json'
FAKE_FILE_NAME = 'prefs_override.json'
OPERA_FOLDER_NAME = 'Opera'
OPERA_APPDATA_FOLDER_NAME = 'Opera Software'

def get_appdata_path() -> str:
	path = os.getenv('APPDATA')
	if OPERA_APPDATA_FOLDER_NAME in os.listdir(path):
		return os.path.join(path, OPERA_APPDATA_FOLDER_NAME)
	else:
		raise ArgumentError('Can\'t find Opera\'s APPDATA folder')
		
def get_fake_file_path() -> str:
	path = get_appdata_path()
	file_recursive_path = os.path.join(path, '**', FAKE_FILE_NAME)
	for file_path in glob.glob(file_recursive_path, recursive=True):
		return file_path
	raise ArgumentError('Can\'t find {0} file'.format(FAKE_FILE_NAME))

def change_base_file_content() -> None:
	path = get_appdata_path()
	message = 'Nothing to do'
	file_recursive_path = os.path.join(path, '**', FILENAME)
	fake_file_path = get_fake_file_path()
	for file_path in glob.glob(file_recursive_path, recursive=True):
		try:
			if os.stat(file_path)[stat.ST_MODE] & stat.S_IWRITE > 0:	# file is NOT set to readonly
				shutil.move(file_path, file_path + '.old')
				shutil.copy(fake_file_path, file_path)
				os.chmod(file_path, stat.S_IREAD)
				message = 'Success'
		except IOError as e:
			print(e)
			
	print('Change base file:\t{0}'.format(message))

def change_backup_files() -> None:
	for path_env in ['ProgramFiles(x86)', 'ProgramW6432']:
		base_path = os.getenv(path_env)
		path = os.path.join(base_path, OPERA_FOLDER_NAME)
		change_backup_files_from_folder(path)
	
def change_backup_files_from_folder(folder_path: str) -> None:
	message = 'Nothing to do'
	file_recursive_path = os.path.join(folder_path, '**', FILENAME)
	fake_file_path = get_fake_file_path()
	for file_path in glob.glob(file_recursive_path, recursive=True):
		try:
			shutil.copy(fake_file_path, file_path)
			os.chmod(file_path, stat.S_IREAD)
			message = 'Success'
		except OSError:
			pass
	print('Backup files deleted:\t{0}\t{1}'.format(message, folder_path))
	
def main() -> None:
	change_base_file_content()
	change_backup_files()
	print('Finished')
	
if __name__ == '__main__':
	try:
		main()
	except PermissionError as e:
		print(e)
		print('You need to run it as Administrator')
	except ArgumentError as e:
		print(e)
	except Exception as e:
		print(e)