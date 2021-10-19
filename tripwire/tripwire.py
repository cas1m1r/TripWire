from threading import Thread
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
		arch = utils.cmd('arch',False).pop().decode()
		# if on raspberry pi or other 32bit systems use:
		# gcc -shared -fPIC -mbe32 -o tripwirelib.so wiretap.c
		if arch == 'x86_64':
			cpile = 'gcc -shared -fPIC -o tripwirelib.so wiretap.c'
		elif arch == 'armv7l':
			cpile = 'gcc -shared -fPIC -mbe32 -o tripwirelib.so wiretap.c'
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
		lmod = timestamps[filename]['modified']
		lacc = timestamps[filename]['opened']	
		if laccessed != timestamps[filename]['opened']:
			timestamps[filename]['wasOpened'] = True
			timestamps[filename]['opened'] = laccessed
			changes = True
		if lmodified != timestamps[filename]['modified']:
			timestamps[filename]['wasModified'] = True
			timestamps[filename]['modified'] = lmodified
			changes = True
	return timestamps, changes

def setupFileListCLI():
	adding = True
	filenames = []
	while adding:
		f = str(raw_input('Enter a file to monitor [Or enter q to quit]:\n'))
		if os.path.isfile(f):
			filenames.append(f)
		elif f.upper() == 'Q':
			adding = False
		else:
			print('[!] Unable to find that file')
	return filenames

def setupFileListGUI():
	cmd = "zenity --file-selection"
	return utils.cmd(cmd,False)

## End of Utility Methods

class TripWire:

	def __init__(self, targetFiles):
		self.dstart, self.tstart = utils.create_timestamp()
		# setup which files to be watching
		self.lib = load_tripwires()
		self.targets = self.checkfiles(targetFiles)
		self.watching = True
		

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
			else:
				print('[!] Unable to find: %s' % filename)	
		return filesFound

	def __str__(self):
		return json.dumps(self.targets)

	def run(self):
		try:
			while self.watching:
				file_list = utils.swap('filelist.txt',False)
				try:
					self.targets, status = verifyFiles(self.lib, self.targets)
					if status:
						self.findChangedFile()
					# kinda thrashing the CPU 
					time.sleep(1)
				except KeyboardInterrupt:
					print('[!] Error Checking Files')
					self.watching = False
					pass
		except KeyboardInterrupt:
			pass


	def findChangedFile(self):
		for fname in self.targets.keys():
			if self.targets[fname]['wasOpened']:
				print('\033[1m[!]\033[31m %s was Opened \033[0m' % fname)
				self.targets[fname]['wasOpened'] = True
			if self.targets[fname]['wasModified']:
				print('\033[1m[!]\033[31m %s was Modified \033[0m' % fname)
				self.targets[fname]['wasModified'] = True


def main():
	if not os.path.isfile(os.path.join(os.getcwd(),'filelist.txt')):
		if '-cli' in sys.argv:
			file_list = setupFileListCLI()
		else:
			file_list = setupFileListGUI()
	else:
		file_list = utils.swap('filelist.txt',False)

	# Now setup the tripwire to monitor the filelist
	agent = TripWire(file_list)
	agent.run()

if __name__ == '__main__':
	main()
