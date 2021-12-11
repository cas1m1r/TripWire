import multiprocessing
from tqdm import tqdm
from ctypes import *
import datetime
import utils
import json
import time 
import sys 
import os

# Load the WatchTower C Library which allows use to interact with linux kernel api
lb = utils.load_library('curious.c', 'watchtower.so')

def getLastModified(target):
	cbuff = create_string_buffer(25)
	lb.lastModified(target, cbuff)
	return utils.cbuff2timestamp(cbuff)	

def getLastOpened(target):
	cbuff = create_string_buffer(25)
	lb.lastOpened(target, cbuff)
	return utils.cbuff2timestamp(cbuff)

def getLastAccessed(target):
	cbuff = create_string_buffer(25)
	lb.lastAccessed(target, cbuff)
	return utils.cbuff2timestamp(cbuff)

def file2json(target):
	accessed = getLastAccessed(target)
	modified = getLastModified(target)
	opened = getLastOpened(target)
	nlinks = lb.getNumLinks(target)
	fuid = lb.getFileUID(target)
	file_info = {'filename': target,
				 'last accessed': str(accessed),
				 'last modified': str(modified),
				 'last opened': str(opened),
				 'n links':nlinks,
				 'fuid':fuid}
	return file_info

def validate_file(states, filename):
	alert_state = states[filename]
	current_state = file2json(filename)
	# if any field in current state doesnt match, return false
	modified =  alert_state['last accessed'] == current_state['last accessed']
	# update the state regardless
	states[filename] = current_state
	return modified, states


class Tower:
	filesystem = {'directories': [], 'file': []}

	def __init__(self, hostname, options):
		# Initialize some defaults for required variables
		self.path  = '/home/%s' % hostname
		self.username = hostname
		self.shutdown = False
		self.verbose = True
		self.n_threads = 5
		self.dt = str(0.0)
		# Check if any options were given
		self.configure(options)
		# Index files to track
		self.index_filesystem()
		# setup initial states for each file
		self.fs = self.setup()
		# Starting Monitoring
		# TODO: Write Monitor Loop [Similar to setup]
		self.monitor()

	def configure(self, opts):
		# Check if user has set verbosity level
		if 'verbose' in opts.keys():
			self.verbose = opts['verbose']

		# Check if user has defined which path(s) to mointor
		if 'path' in opts.keys():
			self.path = opts['path']
			if self.verbose:
				print('[>] Path Changed to: %s' % self.path)
		
		# check whether user has specified number of threads to use
		if 'threads' in opts.keys():
			self.n_threads = opts['threads']
			if self.verbose:
				print('[>] Using %d Threads' % self.n_threads)
		

	def index_filesystem(self):
		if self.verbose:
			print('[+] Searching for all files and directories at %s' % self.path)
		self.filesystem = utils.find_all_files(self.path)
		if self.verbose:
			print('[-] Found %d Files ' % len(self.filesystem['file']))
			print('[-] Found %d Directories ' % len(self.filesystem['directory']))


	def setup(self):
		states = {}
		startpt = time.time()
		pool = multiprocessing.Pool(self.n_threads)
		# Generally finishes in 45-50s and averages ~5000 files/sec using 15 threads
		for file in tqdm(self.filesystem['file']):
			file_check = pool.apply_async(file2json,(file,))
			# For each file:
			#  - check file size
			#  - check user id [UID]
			#  - check when last opened
			#  - check when last accessed
			#  - check when last modified
			#  - check number of symbolic links
			states[file] = file_check.get(1)
		# Keep Track of how long this process takes
		self.dt = str(time.time() - startpt)
		if self.verbose:
			print('[>] Finished Checking All Files [%ss elapsed]' % self.dt)
		return states
	
	def monitor(self):
		startpt = time.time()
		# pool = multiprocessing.Pool(int(self.n_threads/3))
		try:
			while not self.shutdown:
				# Iterate through every file indexed
				for filename in self.filesystem['file']:
					try:
						# comparison = pool.apply_async(validate_file, (self.fs, filename))
						# modified, self.fs = comparison.get(1)
						modified, self.fs = validate_file(self.fs, filename)
						if modified:
							print('[x] %s touched!' % filename)
					except KeyError:
						pass
				time.sleep(0.01)

		except KeyboardInterrupt:
			self.shutdown = True


def main():
	uname = utils.cmd('whoami',False).pop()
	options = {'threads': 15}
	if '-p' in sys.argv:
		ind = 0
		for arg in sys.argv:
			if arg == '-p':
				options['path'] = sys.argv[ind+1]
			ind += 1

	watchman = Tower(uname, options)
	

if __name__ == '__main__':
	main()