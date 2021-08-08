import multiprocessing
from ctypes import *
import datetime
import utils
import json
import time
import sys
import os

yr = 2021
csrc = 'tripwirelib.so'
csrcWin = 'wirelib.dll'
months = {b'Jan':1,b'Feb':2,
		  b'Mar':3,b'Apr':4,
		  b'May':5,b'Jun':6,
		  b'Jul':7,b'Aug':8,
		  b'Sep':9,b'Oct':10,
		  b'Nov':11,b'Dec':12}

### Utility Methods 
def load_tripwires():
	if os.name == 'posix':
		compile_linux()
		return cdll.LoadLibrary("./%s" % csrc)
	elif os.name == 'nt':
		if not os.path.isfile(csrcWin):
			print('[!] Missing %s' % csrcWin)
		return cdll.LoadLibrary(csrcWin)
	else:
		print('[!] OS not supported :(')
		exit()

def compile_linux():
	if not os.path.isfile(csrc) and os.path.isfile('wiretap.c'):
		cpile = 'gcc -shared -fPIC -o tripwirelib.so wiretap.c'
		os.system(cpile)

def cbuff2timestamp(cbuff):
	last = cbuff.raw.split(b'\x00')[0]
	t = last.split(b' ')[-1].split(b':')
	mon = months[last.split(b' ')[0]]
	day = int(last.split(b' ')[1])
	return datetime.datetime(yr,mon,day, int(t[0]), int(t[1]))

def getLastModified(lb, target):
	cbuff = create_string_buffer(32)
	lb.lastModified(target, cbuff)
	return cbuff2timestamp(cbuff)	

def getLastOpened(lb, target):
	cbuff = create_string_buffer(32)
	lb.lastOpened(target, cbuff)
	return cbuff2timestamp(cbuff)

def currentDatetime():
	 ld,lt = utils.create_timestamp()
	 mon = int(ld.split('/')[0])
	 day = int(ld.split('/')[1])
	 yr = int(ld.split('/')[2])
	 hr = int(lt.split(':')[0])
	 mn = int(lt.split(':')[1])
	 sec = int(lt.split(':')[2])
	 return datetime.datetime(yr,mon,day,hr,mn,sec)

def verifyFiles(lb,timestamps):
	changes = False
	now = currentDatetime()
	for filename in timestamps.keys():
		lmodified = getLastModified(lb,filename)
		laccessed = getLastOpened(lb,filename)
		if laccessed != timestamps[filename]['opened']:
			timestamps[filename]['wasOpened'] = True
			timestamps[filename]['opened'] = laccessed
			changes = True
		if lmodified != timestamps[filename]['modified']:
			timestamps[filename]['wasModified'] = True
			timestamps[filename]['modified'] = lmodified
			changes = True
	return timestamps, changes

def setupFileList():
	adding = True
	filenames = []
	while adding:
		f = str(raw_input('Enter a file to monitor [Or enter q to quit]:\n'))
		if os.path.isfile(f):
			filenames.append(f)
		else:
			print('[!] Unable to find that file')
		if f.upper() == 'Q':
			adding = False
	return filenames
## End of Utility Methods

class TripWire:

	def __init__(self, targetFiles):
		self.dstart, self.tstart = utils.create_timestamp()
		# setup which files to be watching
		self.lib = load_tripwires()
		self.targets = self.checkfiles(targetFiles)
		self.watching = True
		
		# run it
		self.run()

	def checkfiles(self, filesIn):
		filesFound = {}
		for filename in filesIn:
			if os.path.isfile(filename):
				filesFound[filename] = {}
				filesFound[filename]['added'] = currentDatetime()
				filesFound[filename]['opened'] = getLastOpened(self.lib,filename)
				filesFound[filename]['modified'] = getLastModified(self.lib,filename)
				filesFound[filename]['wasOpened'] = False
				filesFound[filename]['wasModified'] = False
		return filesFound

	def __str__(self):
		return json.dumps(self.targets)

	def run(self):
		try:
			while self.watching:
				try:
					self.targets, status = verifyFiles(self.lib, self.targets)
					if status:
						self.findChangedFile(self.targets)
				except multiprocessing.TimeoutError:
					print('[!] Error Checking Files')
					pass
		except KeyboardInterrupt:
			pass

	def findChangedFile(self, fdict):
		for fname in fdict.keys():
			if fname not in self.targets.keys():
				continue
			if fdict[fname]['wasOpened']:
				print('\033[1m[!]\033[31m %s was Opened \033[0m' % fname)
				self.targets[fname]['wasOpened'] = True
			if fdict[fname]['wasModified']:
				print('\033[1m[!]\033[31m %s was Modified \033[0m' % fname)
				self.targets[fname]['wasModified'] = True


def main():
	if not os.path.isfile(os.path.join(os.getcwd(),'filelist.txt')):
		try:
			file_list = setupFileList()
		except KeyboardInterrupt:
			pass
	else:
		file_list = utils.swap('filelist.txt',False)

	# Now setup the tripwire to monitor the filelist
	agent = TripWire(file_list)

if __name__ == '__main__':
	main()