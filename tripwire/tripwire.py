from dotenv import load_dotenv
from threading import Thread
from disco import DiscordMsg
from ctypes import *
import datetime
import utils
import json
import time
import sys
import os

<<<<<<< HEAD

INSTALL_PATH = './'
=======
load_dotenv()
>>>>>>> 36e593b0fcc4342e27df613ec55d9124f6a88778
yr = 2021
csrc = os.path.join(INSTALL_PATH,'tripwirelib.so')
csrcWin = os.path.join(INSTALL_PATH,'wirelib.dll')
sys.path.insert(0,INSTALL_PATH)
load_dotenv()

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
		return cdll.LoadLibrary("%s" % csrc)
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
	cbuff = create_string_buffer(21)
	lb.lastModified(target, cbuff)
	return cbuff2timestamp(cbuff)	

def getLastOpened(lb, target):
	cbuff = create_string_buffer(21)
	lb.lastOpened(target, cbuff)
	return cbuff2timestamp(cbuff)

def getLastAccessed(lb, target):
	cbuff = create_string_buffer(21)
	lb.lastAccessed(target, cbuff)
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
		lopened = getLastOpened(lb,filename)
		laccessed = getLastAccessed(lb, filename)
		# For Debugging:
		# print(f'{filename}  {lmodified}  {laccessed}  {lopened} ')
		if lopened != timestamps[filename]['opened']:
			timestamps[filename]['wasOpened'] = True
			timestamps[filename]['opened'] = lopened
			changes = True
		if lmodified != timestamps[filename]['modified']:
			timestamps[filename]['wasModified'] = True
			timestamps[filename]['modified'] = lmodified
			changes = True
		if laccessed != timestamps[filename]['accessed']:
			timestamps[filename]['wasAccessed'] = True
			timestamps[filename]['accessed'] = laccessed
			changes = True
		
	return timestamps, changes

def setupFileListCLI():
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

def setupFileListGUI():
	cmd = "zenity --file-selection"
	return utils.cmd(cmd,False)

## End of Utility Methods

class TripWire:

	def __init__(self, targetFiles, useBot):
		self.dstart, self.tstart = utils.create_timestamp()
		# setup which files to be watching
		self.lib = load_tripwires()
		self.targets = self.checkfiles(targetFiles)
		self.watching = True
		# TODO: configure alerting system besides printing to console
		if useBot:
			# report file alerts to a discord bot integration 
			self.hasBot = True
			if not os.path.isdir('.alerts'):
				os.mkdir('.alerts')
		else:
			self.hasBot = True
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
				filesFound[filename]['accessed'] = getLastAccessed(self.lib, filename)
				filesFound[filename]['wasOpened'] = False
				filesFound[filename]['wasModified'] = False
				filesFound[filename]['wasAccessed'] = False
		return filesFound

	def __str__(self):
		return json.dumps(self.targets)

	def run(self):
		try:
			while self.watching:
				try:
					time.sleep(.1)
					self.targets, status = verifyFiles(self.lib, self.targets)
					if status:
						filesTouched = self.findChangedFile()
						# alert discord bot if integrated
						if self.hasBot:
							msg = '**Files Accessed:**\n```%s```' % '\n'.join(filesTouched)
							print('[>] Sending Discord Message')
							data = {'content': 
									msg}
							DiscordMsg('text', data).send_message()
							continue
						# self.targets = self.checkfiles(list(self.targets.keys()))
				except KeyboardInterrupt:
					print('[!] Error Checking Files')
					self.watching = False
					pass
		except KeyboardInterrupt:
			pass


	def findChangedFile(self):
		triggered = []
		for fname in self.targets.keys():
			if self.targets[fname]['wasOpened']:
				print('\033[1m[!]\033[31m %s was Opened \033[0m' % fname)
				self.targets[fname]['wasOpened'] = True
				triggered.append(str(fname))
			if self.targets[fname]['wasModified']:
				print('\033[1m[!]\033[31m %s was Modified \033[0m' % fname)
				self.targets[fname]['wasModified'] = True
				triggered.append(str(fname))
			if self.targets[fname]['wasAccessed']:
				print('\033[1m[!]\033[31m %s was Accessed \033[0m' % fname)
				self.targets[fname]['wasAccessed'] = True
				triggered.append(str(fname))
		return triggered

def main():
	bot = False
	if not os.path.isfile(os.path.join(os.getcwd(),'filelist.txt')):
		if '-cli' in sys.argv:
			file_list = setupFileListCLI()
		else:
			file_list = setupFileListGUI()
	else:
		file_list = utils.swap('filelist.txt',False)

	if '-bot' in sys.argv:
		bot = True


	if '-bg' in sys.argv:
		agent = Thread(target=TripWire, args=(file_list, bot))
		agent.setDaemon(True)
		agent.start()
	else:
		# Now setup the tripwire to monitor the filelist
		agent = TripWire(file_list,bot)

if __name__ == '__main__':
	main()