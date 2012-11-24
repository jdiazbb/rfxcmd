#!/usr/bin/python
# coding=UTF-8

# ----------------------------------------------------------------------------
#	
#	RFXCMD.PY
#	
#	Copyright (C) 2012 Sebastian Sjoholm
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#	
#	Version history can be found at 
#	http://code.google.com/p/rfxcmd/wiki/VersionHistory
#
#	Revision: $Rev$
#	Date: $Date$
#
#	NOTES
#	
#	RFXCOM is a Trademark of RFSmartLink.
#	
# ----------------------------------------------------------------------------

import string
import sys
import os
import time
import binascii
import traceback
import subprocess
import re
import logging

# signalhandler
import signal

from xml.dom.minidom import parseString
import xml.dom.minidom as minidom
from optparse import OptionParser

# Needed for Graphite communication
from socket import socket

# ----------------------------------------------------------------------------
# CONFIG CLASS
# ----------------------------------------------------------------------------

class config_data:
	def __init__(
		self, 
		mysql_server = '',
		mysql_database = '',
		enableall_rf = False,
		undecoded = False,
		mysql_username = "",
		mysql_password = "",
		trigger = False,
		triggerfile = "",
		createpid = False,
		pidfile = "",
		configfile = "",
		rfxcmd_action = "",
		device = "",
		serialport = ""):
        
		self.enableall_rf = enableall_rf
		self.undecoded = undecoded
		self.mysql_server = mysql_server
		self.mysql_database = mysql_database
		self.mysql_username = mysql_username
		self.mysql_password = mysql_password
		self.trigger = trigger
		self.createpid = createpid
		self.pidfile = pidfile
		self.configfile = configfile
		self.rfxcmd_action = rfxcmd_action
		self.device = device
		self.serialport = serialport

# ----------------------------------------------------------------------------
# INIT OBJECTS
# ----------------------------------------------------------------------------

config = config_data()      

# ----------------------------------------------------------------------------
# LOG DEBUG
# ----------------------------------------------------------------------------

def logdebug(text):
	try:
		logger.debug(text)
	except NameError:
		pass

def logerror(text):
	try:
		logger.error(text)
	except NameError:
		pass

# ----------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------

# Default
loglevel = 'INFO'

if os.path.exists('config.xml'):
	f = open('config.xml','r')
	data = f.read()
	f.close()
	
	try:
		dom = parseString(data)
	except:
		print "Error: problem in the config.xml file, cannot process it"
	
	try:
		xmlTag = dom.getElementsByTagName( 'loglevel' )[0].toxml()
		loglevel = xmlTag.replace('<loglevel>','').replace('</loglevel>','')
	except:
		pass
	
	loglevel = loglevel.upper()
	
	if loglevel == 'DEBUG' or loglevel == 'ERROR':
		logger = logging.getLogger('rfxcmd')
		hdlr = logging.FileHandler('rfxcmd.log')
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		logger.addHandler(hdlr) 
		logger.setLevel(loglevel)
	
# ----------------------------------------------------------------------------
# IMPORT SERIAL
# ----------------------------------------------------------------------------

try:
	logdebug("Import serial extension")
	import serial
	logdebug("Serial extension version: " + serial.VERSION)
except ImportError:
	print "Error: You need to install Serial extension for Python"
	logdebug("Error: Serial extension for Python could not be loaded")
	logdebug("Exit 1")
	sys.exit(1)

# ----------------------------------------------------------------------------
# NAME & VERSION
# ----------------------------------------------------------------------------

sw_name = "RFXCMD"
sw_version = "0.2 (BETA)"

logdebug(sw_name + ' ' + sw_version)

# ----------------------------------------------------------------------------
# DEFAULT CONFIGURATION PARAMETERS
# ----------------------------------------------------------------------------

# If the config.xml does not exist, or can not be loaded, this is the
# default configuration which will be used

config.undecoded = False
config.mysql_server = ""
config.mysql_database = ""
config.mysql_username = ""
config.mysql_password = ""
config.trigger = False
config.sqlite_server = ""
config.sqlite_database = ""
config.sqlite_username = ""
config.sqlite_password = ""
config.graphite_server = ""
config.graphite_port = ""
config.createpid = False
config.pidfile = ""

# ----------------------------------------------------------------------------
# DEAMONIZE
# Credit: George Henze
# ----------------------------------------------------------------------------

def shutdown():
	# clean up PID file after us
	logdebug("Daemon shutdown")
	if config.createpid:
		logdebug("Removing PID file " + str(config.pidfile))
		os.remove(config.pidfile)
    
	logdebug("Exit 0")
	os._exit(0)
    
def handler(signum=None, frame=None):
	if type(signum) != type(None):
		logdebug("Signal %i caught, exiting..." % int(signum))
		shutdown()
        
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)
    
def daemonize():

	try:
		pid = os.fork()
		if pid != 0:
			sys.exit(0)
	except OSError, e:
		raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))

	os.setsid() 

	prev = os.umask(0)
	os.umask(prev and int('077', 8))

	try:
		pid = os.fork() 
		if pid != 0:
			sys.exit(0)
	except OSError, e:
		raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))

	dev_null = file('/dev/null', 'r')
	os.dup2(dev_null.fileno(), sys.stdin.fileno())

	if config.createpid == True:
		pid = str(os.getpid())
		logdebug("Writing PID " + pid + " to " + str(config.pidfile))
		file(config.pidfile, 'w').write("%s\n" % pid)

# ----------------------------------------------------------------------------
# Send data to graphite
# Credit: Frédéric Pégé
# ----------------------------------------------------------------------------

def send_graphite(CARBON_SERVER, CARBON_PORT, lines):

	sock = socket()
	try:
		sock.connect( (CARBON_SERVER,CARBON_PORT) )
	except:
		print "Couldn't connect to %(server)s on port %(port)d, is carbon-agent.py running?" % { 'server':CARBON_SERVER, 'port':CARBON_PORT }
		sys.exit(1)
	
	message = '\n'.join(lines) + '\n' #all lines must end in a newline
	sock.sendall(message)

# ----------------------------------------------------------------------------
# Read x amount of bytes from serial port
# Boris Smus http://smus.com
# ----------------------------------------------------------------------------

def readbytes(number):
	buf = ''
	for i in range(number):
		byte = serialport.read()
		buf += byte

	return buf

# ----------------------------------------------------------------------------
# Convert a byte string to it's hex string representation e.g. for output.
# http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/
#
# * added str() to byteStr in case input data is in integer
# ----------------------------------------------------------------------------

def ByteToHex( byteStr ):
	return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()

# ----------------------------------------------------------------------------
# Return the binary representation of dec_num
# http://code.activestate.com/recipes/425080-easy-binary2decimal-and-decimal2binary/
# Guyon Mor�e http://gumuz.looze.net/
# ----------------------------------------------------------------------------

def Decimal2Binary(dec_num):
	if dec_num == 0: return '0'
	return (Decimal2Binary(dec_num >> 1) + str(dec_num % 2))

# ----------------------------------------------------------------------------
# testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
# http://wiki.python.org/moin/BitManipulation
# ----------------------------------------------------------------------------

def testBit(int_type, offset):
	mask = 1 << offset
	return(int_type & mask)

# ----------------------------------------------------------------------------
# clearBit() returns an integer with the bit at 'offset' cleared.
# http://wiki.python.org/moin/BitManipulation
# ----------------------------------------------------------------------------

def clearBit(int_type, offset):
	mask = ~(1 << offset)
	return(int_type & mask)

# ----------------------------------------------------------------------------
# split_len, split string into specified chunks
# ----------------------------------------------------------------------------

def split_len(seq, length):
	return [seq[i:i+length] for i in range(0, len(seq), length)]

# ----------------------------------------------------------------------------
# Decode packet
# ----------------------------------------------------------------------------

def decodePacket( message ):
		
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
		
	decoded = False
	db = ""
	
	packettype = ByteToHex(message[1])
	subtype = ByteToHex(message[2])
	seqnbr = ByteToHex(message[3])
	id1 = ByteToHex(message[4])
	
	if len(message) > 5:
		id2 = ByteToHex(message[5])
	
	if printout_complete == True:
		print "Packettype\t\t= " + rfx_packettype[packettype]

	# ---------------------------------------
	# 0x0 - Interface Control
	# ---------------------------------------
	if packettype == '00':
		decoded = True
	
	# ---------------------------------------
	# 0x01 - Interface Message
	# ---------------------------------------
	if packettype == '01':
		decoded = True
		
		if printout_complete == True:
			data = {
			'packetlen' : ByteToHex(message[0]),
			'packettype' : ByteToHex(message[1]),
			'subtype' : ByteToHex(message[2]),
			'seqnbr' : ByteToHex(message[3]),
			'cmnd' : ByteToHex(message[4]),
			'msg1' : ByteToHex(message[5]),
			'msg2' : ByteToHex(message[6]),
			'msg3' : ByteToHex(message[7]),
			'msg4' : ByteToHex(message[8]),
			'msg5' : ByteToHex(message[9]),
			'msg6' : ByteToHex(message[10]),
			'msg7' : ByteToHex(message[11]),
			'msg8' : ByteToHex(message[12]),
			'msg9' : ByteToHex(message[13])
			}

			# Subtype
			if data['subtype'] == '00':
				print "Subtype\t\t\t= Interface response"
			else:
				print "Subtype\t\t\t= Unknown type (" + data['packettype'] + ")"
		
			# Seq
			print "Sequence nbr\t\t= " + data['seqnbr']
		
			# Command
			print "Response on cmnd\t= " + rfx_cmnd[data['cmnd']]
		
			# MSG 1
			print "Transceiver type\t= " + rfx_subtype_01_msg1[data['msg1']]
		
			# MSG 2
			print "Firmware version\t= " + str(int(data['msg2'],16))
			
			if testBit(int(data['msg3'],16),7) == 128:
				print "Display undecoded\t= On"
			else:
				print "Display undecoded\t= Off"

			print "Protocols:"
		
			# MSG 3
			if testBit(int(data['msg3'],16),0) == 1:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['1']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['1']
				
			if testBit(int(data['msg3'],16),1) == 2:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['2']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['2']
				
			if testBit(int(data['msg3'],16),2) == 4:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['4']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['4']
				
			if testBit(int(data['msg3'],16),3) == 8:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['8']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['8']
				
			if testBit(int(data['msg3'],16),4) == 16:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['16']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['16']
				
			if testBit(int(data['msg3'],16),5) == 32:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['32']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['32']
				
			if testBit(int(data['msg3'],16),6) == 64:
				print "Enabled\t\t\t" + rfx_subtype_01_msg3['64']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg3['64']
		
			# MSG 4
			if testBit(int(data['msg4'],16),0) == 1:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['1']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['1']

			if testBit(int(data['msg4'],16),1) == 2:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['2']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['2']

			if testBit(int(data['msg4'],16),2) == 4:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['4']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['4']

			if testBit(int(data['msg4'],16),3) == 8:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['8']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['8']

			if testBit(int(data['msg4'],16),4) == 16:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['16']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['16']

			if testBit(int(data['msg4'],16),5) == 32:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['32']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['32']

			if testBit(int(data['msg4'],16),6) == 64:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['64']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['64']

			if testBit(int(data['msg4'],16),7) == 128:
				print "Enabled\t\t\t" + rfx_subtype_01_msg4['128']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg4['128']

			# MSG 5
			if testBit(int(data['msg5'],16),0) == 1:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['1']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['1']

			if testBit(int(data['msg5'],16),1) == 2:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['2']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['2']

			if testBit(int(data['msg5'],16),2) == 4:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['4']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['4']

			if testBit(int(data['msg5'],16),3) == 8:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['8']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['8']

			if testBit(int(data['msg5'],16),4) == 16:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['16']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['16']

			if testBit(int(data['msg5'],16),5) == 32:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['32']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['32']

			if testBit(int(data['msg5'],16),6) == 64:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['64']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['64']

			if testBit(int(data['msg5'],16),7) == 128:
				print "Enabled\t\t\t" + rfx_subtype_01_msg5['128']
			else:
				print "Disabled\t\t" + rfx_subtype_01_msg5['128']
		
	# ---------------------------------------
	# 0x02 - Receiver/Transmitter Message
	# ---------------------------------------
	if packettype == '02':
		
		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_02[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Message\t\t\t= " + rfx_subtype_02_msg1[id1]
		
		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;\n" %
							(timestamp, packettype, subtype, seqnbr, id1 ) )

	# ---------------------------------------
	# 0x10 Lighting1
	# ---------------------------------------
	if packettype == '10':

		decoded = True
		
		signal = str(int(ByteToHex(message[7]),16) >> 4)

		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_10[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Housecode\t\t= " + ByteToHex(message[4])
			print "Unitcode\t\t= " + ByteToHex(message[5])
			print "Command\t\t\t= " + ByteToHex(message[6])
			print "Signal level\t\t= " + signal

	# ---------------------------------------
	# 0x11 Lighting2
	# ---------------------------------------
	if packettype == '11':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_11[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6]) + ByteToHex(message[7])
			print "Unitcode\t\t= " + ByteToHex(message[8])
			print "Command\t\t\t= " + rfx_subtype_11_cmnd[ByteToHex(message[9])]
			print "Level\t\t\t= " + ByteToHex(message[10])
			
			signal_level = str(int(ByteToHex(message[11]),16) & 0xf)
			print "Signal level\t\t\t= " + signal_level
			
	# ---------------------------------------
	# 0x12 Lighting3
	# ---------------------------------------
	if packettype == '12':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_12[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "System\t\t\t= " + ByteToHex(message[4])
			# TODO

	# ---------------------------------------
	# 0x13 Lighting4
	# ---------------------------------------
	if packettype == '13':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_13[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x14 Lighting5
	# ---------------------------------------
	if packettype == '14':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_14[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x15 Lighting6
	# Credit: Dimitri Clatot
	# ---------------------------------------
	if packettype == '15':

		decoded = True

		groupcode = ByteToHex(message[6])
		unitcode = ByteToHex(message[7])
		command = ByteToHex(message[8])
		command_seqnbr = ByteToHex(message[9])
		rfu = str(int(ByteToHex(message[10]), 16))
		signal = str(int(ByteToHex(message[11]),16) >> 4)

		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_15[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "ID\t\t\t= "  + id1 + id2
			print "Groupcode\t\t= " + rfx_subtype_15_groupcode[groupcode]
			print "Unitcode\t\t= " + ByteToHex(message[7])
			print "Command\t\t\t= " + rfx_subtype_15_cmnd[command]
			print "Command seqnbr\t\t= " + ByteToHex(message[9])
			print "RFU\t\t\t= " + rfu
			print "Signal level\t\t= " + signal

		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %(timestamp,
							packettype, subtype, seqnbr, id1, id2,
							rfx_subtype_15_groupcode[groupcode], unitcode,
							rfx_subtype_15_cmnd[command], command_seqnbr, rfu, signal ) )

	# ---------------------------------------
	# 0x18 Curtain1 (Transmitter only)
	# ---------------------------------------
	if packettype == '18':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_18[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x19 Blinds1
	# ---------------------------------------
	if packettype == '19':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_19[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x20 Security1
	# Credit: Dimitri Clatot
	# ---------------------------------------
	if packettype == '20':

		decoded = True
		
		id3 = ByteToHex(message[6])
		status = ByteToHex(message[7])
		signal = int(ByteToHex(message[8]),16) >> 4
		battery = int(ByteToHex(message[8]),16) & 0xf

		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_20[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "ID1\t\t\t= "  + id1
			print "ID2\t\t\t= "  + id2
			print "ID3\t\t\t= "  + id3
			print "Status\t\t\t= " + rfx_subtype_20_status[status]
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2, id3,
							rfx_subtype_20_status[status], str(battery), str(signal) ) )

	# ---------------------------------------
	# 0x28 Curtain1
	# ---------------------------------------
	if packettype == '28':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_28[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x30 Remote control and IR
	# ---------------------------------------
	if packettype == '30':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_30[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x40 - Thermostat1
	# ---------------------------------------
	if packettype == '40':

		decoded = True

		temp = ByteToHex(message[6])
		temp_set = ByteToHex(message[7])
		temp_status = ByteToHex(message[8])

		temperature = int(temp,16)
		temperature_set = int(temp_set,16)

		if temp_status == '0D' or temp_status == '01':
			status = "Demand"
		elif temp_status == '0E' or temp_status == '02':
			status = "No Demand"
		elif temp_status == '0F' or temp_status == '03':
			status = "Initializing"
		else:
			status = "Unknown"

		signal = int(ByteToHex(message[9]),16) >> 4
		battery = int(ByteToHex(message[9]),16) & 0xf

		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_40[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1\t\t\t= " + id1
			print "Id 2\t\t\t= " + id2

			print "Temperature\t\t= " + str(temperature) + " C"
			print "Temperature set\t\t= " + str(temperature_set) + " C"
			print "Status\t\t\t= " + status

			print "Battery (0-15)\t\t= " + str(battery)
			print "Signal level (0-7)\t= " + str(signal)

			if printout_csv == True:
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
				(timestamp, packettype, subtype, seqnbr, id1, id2,
				temperature, temperature_set, status, str(battery), str(signal) ) )

			if options.mysql:
				try:
					db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
					cursor = db.cursor()

					cursor.execute("INSERT INTO thermostat \
					(datetime, packettype, subtype, seqnbr, id1, id2, temperature, temperature_set, status, battery, signal_level) VALUES \
					('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
					(timestamp, packettype, subtype, seqnbr, id1, id2, temperature, temperature_set, status, battery, signal))

					db.commit()

				except MySQLdb.Error, e:
					print "Error %d: %s" % (e.args[0], e.args[1])
					sys.exit(1)

				finally:
					if db:
						db.close()


	# ---------------------------------------
	# 0x41 Thermostat2
	# ---------------------------------------
	if packettype == '41':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_41[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x42 Thermostat3
	# ---------------------------------------
	if packettype == '42':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_42[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x50 - Temperature sensors
	# ---------------------------------------
	if packettype == '50':
	
		decoded = True
		temp_high = ByteToHex(message[6])
		temp_low = ByteToHex(message[7])
		
		polarity = testBit(int(temp_high,16),7)

		if polarity == 128:
			polarity_sign = "-"
		else:
			polarity_sign = ""

		temp_high = clearBit(int(temp_high,16),7)
		temp_high = temp_high << 8
		temperature = ( temp_high + int(temp_low,16) ) * 0.1
		temperature_str = polarity_sign + str(temperature)

		signal = int(ByteToHex(message[8]),16) >> 4
		battery = int(ByteToHex(message[8]),16) & 0xf
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_50[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1\t\t\t= " + id1
			print "Id 2\t\t\t= " + id2
			
			print "Temperature\t\t= " + temperature_str + " C"
			
			print "Battery (0-9)\t\t= " + str(battery)
			print "Signal level (0-15)\t= " + str(signal)

		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							temperature_str, str(battery), str(signal) ) )

		if options.mysql:

			try:

				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, temperature, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, temperature_str, battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:

				print "Error: (MySQL Query) %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:

				if db:
					db.close()

		if options.sqlite:
			try:
				cx = sqlite3.connect(config.sqlite_database)
				cu = cx.cursor()
				sql = """
					INSERT INTO weather (datetime, packettype, subtype, seqnbr, id1, id2, temperature, battery, signal_level)
					VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s')
					""" % (timestamp, packettype, subtype, seqnbr, id1, id2, temperature_str, battery, signal)

				cu.execute(sql)
				cx.commit()
				
			except sqlite3.Error, e:
			
				print "Error: (SQLite Query) " + str(e)
				sys.exit(1)
			
			finally:
				cx.close()

	# ---------------------------------------
	# 0x51 - Humidity sensors
	# ---------------------------------------

	if packettype == '51':
		
		decoded = True

		# Humidity
		humidity = ByteToHex(message[6])
		humidity_status = ByteToHex(message[7])

		# Battery & Signal
		batt_rssi = ByteToHex(message[8])		
		signal = int(batt_rssi,16) >> 4
		battery = int(batt_rssi,16) & 0xf
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_51[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1 (House)\t\t= " + id1
			print "Id 2 (Channel)\t\t= " + id2
			
			print "Humidity\t\t= " + str(int(humidity,16))
			
			if humidity_status == '00':
				print "Humidity Status\t\t= Dry"
			elif humidity_status == '01':
				print "Humidity Status\t\t= Comfort"
			elif humidity_status == '02':
				print "Humidity Status\t\t= Normal"
			elif humidity_status == '03':
				print "Humidity Status\t\t= Wet"
			else:
				print "Humidity Status\t\t= Unknown"
			
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
		
		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							str(int(humidity,16)), humidity_status, 
							str(battery), str(signal)) )
		
		if options.mysql:

			try:
				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, humidity, humidity_status, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, int(humidity,16), int(humidity_status,16), \
				battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:
				if db:
					db.close()
					
	# ---------------------------------------
	# 0x52 - Temperature and humidity sensors
	# ---------------------------------------
	if packettype == '52':
		
		decoded = True

		# Temperature
		temp_high = ByteToHex(message[6])
		temp_low = ByteToHex(message[7])
		polarity = testBit(int(temp_high,16),7)
		
		if polarity == 128:
			polarity_sign = "-"
		else:
			polarity_sign = ""
			
		temp_high = clearBit(int(temp_high,16),7)
		temp_high = temp_high << 8
		temperature = ( temp_high + int(temp_low,16) ) * 0.1
		temperature_str = polarity_sign + str(temperature)
		
		# Humidity
		humidity = ByteToHex(message[8])
		humidity_status = ByteToHex(message[9])

		# Battery & Signal
		batt_rssi = ByteToHex(message[10])		
		signal = int(batt_rssi,16) >> 4
		battery = int(batt_rssi,16) & 0xf
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_52[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1 (House)\t\t= " + id1
			print "Id 2 (Channel)\t\t= " + id2
			
			print "Temperature\t\t= " + temperature_str + " C"
			print "Humidity\t\t= " + str(int(humidity,16))
			
			if humidity_status == '00':
				print "Humidity Status\t\t= Dry"
			elif humidity_status == '01':
				print "Humidity Status\t\t= Comfort"
			elif humidity_status == '02':
				print "Humidity Status\t\t= Normal"
			elif humidity_status == '03':
				print "Humidity Status\t\t= Wet"
			else:
				print "Humidity Status\t\t= Unknown"
			
			print "Battery (0-9)\t\t= " + str(battery)
			print "Signal level (0-15)\t= " + str(signal)
		
		if printout_csv == True:
		
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							temperature_str, str(int(humidity,16)), humidity_status, 
							str(battery), str(signal)) )
		
		if options.graphite == True:
			now = int( time.time() )
			linesg=[]
			linesg.append("%s.%s.temperature %s %d" % ( id1, id2, temperature_str,now))
			linesg.append("%s.%s.humidity %s %d" % ( id1, id2, humidity,now))
			linesg.append("%s.%s.battery %s %d" % ( id1, id2, battery,now))
			linesg.append("%s.%s.signal %s %d"% ( id1, id2, signal,now))
			send_graphite(config.graphite_server, config.graphite_port, linesg)

		if options.mysql:

			try:
				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, temperature, humidity, humidity_status, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, temperature_str, int(humidity,16), int(humidity_status,16), \
				battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:
				if db:
					db.close()

	# ---------------------------------------
	# 0x54 - Temperature, humidity and barometric sensors
	# Credit: Jean-Baptiste Bodart
	# ---------------------------------------
	if packettype == '54':
		
		decoded = True

		# Temperature
		temp_high = ByteToHex(message[6])
		temp_low = ByteToHex(message[7])
		polarity = testBit(int(temp_high,16),7)
		
		if polarity == 128:
			polarity_sign = "-"
		else:
			polarity_sign = ""
			
		temp_high = clearBit(int(temp_high,16),7)
		temp_high = temp_high << 8
		temperature = ( temp_high + int(temp_low,16) ) * 0.1
		temperature_str = polarity_sign + str(temperature)
		
		# Humidity
		humidity = ByteToHex(message[8])
		humidity_status = ByteToHex(message[9])

		# Barometric pressure
		barometric_high = ByteToHex(message[10])
		barometric_low = ByteToHex(message[11])
		barometric_high = clearBit(int(barometric_high,16),7)
		barometric_high = barometric_high << 8
		barometric = ( barometric_high + int(barometric_low,16) )
		
		# Forecast
		forecast_status = ByteToHex(message[12])
		
		# Battery & Signal
		batt_rssi = ByteToHex(message[13])		
		signal = int(batt_rssi,16) >> 4
		battery = int(batt_rssi,16) & 0xf
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_54[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1 (House)\t\t= " + id1
			print "Id 2 (Channel)\t\t= " + id2
			
			print "Temperature\t\t= " + temperature_str + " C"
			print "Humidity\t\t= " + str(int(humidity,16))
			
			if humidity_status == '00':
				print "Humidity Status\t\t= Dry"
			elif humidity_status == '01':
				print "Humidity Status\t\t= Comfort"
			elif humidity_status == '02':
				print "Humidity Status\t\t= Normal"
			elif humidity_status == '03':
				print "Humidity Status\t\t= Wet"
			else:
				print "Humidity Status\t\t= Unknown"
			
			print "Barometric pressure\t= " + str(barometric)
			
			if forecast_status == '01':
				print "Forecast Status\t\t= Sunny"
			elif forecast_status == '02':
				print "Forecast Status\t\t= Partly cloudy"
			elif forecast_status == '03':
				print "Forecast Status\t\t= Cloudy"
			elif forecast_status == '04':
				print "Forecast Status\t\t= Rainy"
			else:
				print "Forecast Status\t\t= Unknown"
			
			print "Battery (0-9)\t\t= " + str(battery)
			print "Signal level (0-15)\t= " + str(signal)
		
		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							temperature_str, str(int(humidity,16)), humidity_status, 
							str(barometric), forecast_status, str(battery), str(signal)) )
		
		if options.mysql:

			try:
				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, temperature, humidity, humidity_status, barometric, forecast, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s', '%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, temperature_str, int(humidity,16), int(humidity_status,16), \
				barometric, int(forecast_status,16), battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:
				if db:
					db.close()

	# ---------------------------------------
	# 0x55 - Rain sensors
	# ---------------------------------------
	
	if packettype == '55':
		
		decoded = True

		# Rain rate
		rainrate_high = ByteToHex(message[6])
		rainrate_low = ByteToHex(message[7])

		# Rain total
		raintotal1 = ByteToHex(message[8])
		raintotal2 = ByteToHex(message[9])
		raintotal3 = ByteToHex(message[10])
		
		# Battery & Signal	
		signal = int(ByteToHex(message[11]),16) >> 4
		battery = int(ByteToHex(message[11]),16) & 0xf
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_55[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1 (House)\t\t= " + id1
			print "Id 2 (Channel)\t\t= " + id2
			
			if subtype == '1':
				print "Rain rate\t\t= Not implemented in rfxcmd, need example"
			elif subtype == '2':
				print "Rain rate\t\t= Not implemented in rfxcmd, need example"
			else:
				print "Rain rate\t\t= Not supported"

			print "Raintotal:\t\t= " + str(int(raintotal1,16))
			print "Raintotal:\t\t= " + str(int(raintotal2,16))
			print "Raintotal:\t\t= " + str(int(raintotal3,16))
				
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
		
		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							( timestamp, packettype, subtype, seqnbr, id1, id2,
							str(int(rainrate_high,16)), str(int(raintotal1,16)), 
							str(battery), str(signal) ) )

		if options.mysql:
			try:
				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, rainrate, raintotal, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, int(rainrate_high,16), int(raintotal1,16), \
				battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:
				if db:
					db.close()

	# ---------------------------------------
	# 0x56 - Wind sensors
	# ---------------------------------------
	if packettype == '56':
		
		decoded = True

		# Direction (6 & 7)
		direction_high = int(ByteToHex(message[6]), 16)
		direction_low = int(ByteToHex(message[7]), 16)
		if direction_high <> 0:
			direction_high = direction_high + 255
		direction = direction_high + direction_low
		direction_str = str(direction)
		
		# AV Speed (8 & 9) (not used in WIND5)
		if subtype <> "05":
			av_high = ByteToHex(message[8])
			av_low = ByteToHex(message[9])
			av = ( int(av_high,16) + int(av_low,16) ) * 0.1
			av_str = str(av)
		else:
			av_str = "0";
			
		# Gust (10 & 11)
		gust_high = ByteToHex(message[10])
		gust_low = ByteToHex(message[11])
		gust = ( int(gust_high,16) + int(gust_low,16) ) * 0.1
		gust_str = str(gust)
		
		# Temperature
		if subtype == "04":
			temp_high = ByteToHex(message[12])
			temp_low = ByteToHex(message[13])
			polarity = testBit(int(temp_high,16),12)
		
			if polarity == 128:
				polarity_sign = "-"
			else:
				polarity_sign = ""

			temp_high = clearBit(int(temp_high,16),7)
			temp_high = temp_high << 8
			temperature = ( temp_high + int(temp_low,16) ) * 0.1
			temperature_str = polarity_sign + str(temperature)
		else:
			temperature_str = "0"

		# Chill factor (14,15)
		if subtype == "04":
			chill_high = ByteToHex(message[14])
			chill_low = ByteToHex(message[15])
			chill_pol = testBit(int(chill_high,16),14)
		
			if chill_pol == 1:
				chill_pol_sign = "-"
			else:
				chill_pol_sign = ""

			chill_high = clearBit(int(chill_high,16),7)
			chill_high = chill_high << 8
			windchill = ( chill_high + int(chill_low,16) ) * 0.1
			windchill_str = chill_pol_sign + str(windchill)
		else:
			windchill_str = "0"
		
		# Battery & Signal
		batt_rssi = ByteToHex(message[16])
		signal = int(batt_rssi,16) >> 4
		battery = int(batt_rssi,16) & 0xf
	
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_56[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1 (House)\t\t= " + id1
			print "Id 2 (Channel)\t\t= " + id2
			
			print "Wind direction\t\t= " + direction_str + " degrees"
			
			if subtype <> "05":
				print "Average wind\t\t= " + av_str + " mtr/sec"
			
			if subtype == "04":
				print "Temperature\t\t= " + temperature_str + " C"
				print "Wind chill\t\t= " + windchill_str + " C" 
			
			print "Windgust\t\t= " + gust_str + " mtr/sec"
			
			print "Battery (0-9)\t\t= " + str(battery)
			print "Signal level (0-15)\t= " + str(signal)

		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							direction_str, av_str, gust_str,
							temperature_str, windchill_str, 
							str(battery), str(signal) ) )
		
		if options.mysql:

			try:
				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, temperature, winddirection, av_speed, \
				windchill, gust, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, temperature_str, direction, av, \
				windchill, gust, battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:
				if db:
					db.close()
	
	# ---------------------------------------
	# 0x5A Energy sensor
	# Credit: Jean-Michel ROY
	# ---------------------------------------
	if packettype == '5A':

		decoded = True

		# Battery & Signal
		signal = int(ByteToHex(message[17]),16) >> 4
		battery = int(ByteToHex(message[17]),16) & 0xf

		# Power
		instant = int(ByteToHex(message[7]), 16) * 0x1000000 + int(ByteToHex(message[8]), 16) * 0x10000 + int(ByteToHex(message[9]), 16) * 0x100  + int(ByteToHex(message[10]), 16)
		usage = int ((int(ByteToHex(message[11]), 16) * 0x10000000000 + int(ByteToHex(message[12]), 16) * 0x100000000 +int(ByteToHex(message[13]), 16) * 0x1000000 + int(ByteToHex(message[14]), 16) * 0x10000 + int(ByteToHex(message[15]), 16) * 0x100 + int(ByteToHex(message[16]), 16) ) / 223.666)

		if printout_complete == True:
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id 1\t\t\t= " + id1
			print "Id 2\t\t\t= " + id2
			print "Instant usage\t\t= " + str(instant) + " Watt"
			print "Total usage\t\t= " + str(usage) + " Wh"
			print "Battery (0-9)\t\t= " + str(battery)
			print "Signal level (0-15)\t= " + str(signal)

		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							str(instant), str(battery), str(signal)) )

		if options.mysql:

			try:
				db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO energy \
				(datetime, packettype, subtype, seqnbr, id1, id2, instant, total, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, instant, usage, battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:
				if db:
					db.close()

	# ---------------------------------------
	# 0x5B Current + Energy sensor
	# ---------------------------------------
	
	# TODO
	
	# ---------------------------------------
	# Not decoded message
	# ---------------------------------------	
	
	# The packet is not decoded, then print it on the screen
	if decoded == False:
		print timestamp + " " + ByteToHex(message)
		print "RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/ReadMe for more information."

	# decodePackage END
	return

# ----------------------------------------------------------------------------
# DECODE THE MESSAGE AND SEND TO RFX
# ----------------------------------------------------------------------------

def send_rfx( message ):
	
	global printout_complete, printout_csv
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	
	if printout_complete == True:
		print "------------------------------------------------"
		print "Send\t\t\t= " + ByteToHex( message )
		print "Date/Time\t\t= " + timestamp
		print "Packet Length\t\t= " + ByteToHex( message[0] )
		try:
			decodePacket( message )
		except KeyError:
			print "Error: unrecognizable packet"
	
	serialport.write( message )
	time.sleep(1)

# ----------------------------------------------------------------------------
# READ DATA FROM RFX AND DECODE THE MESSAGE
# ----------------------------------------------------------------------------

def read_rfx():

	global printout_complete, printout_csv
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	logdebug('Timestamp: ' + timestamp)
	message = None

	try:
		byte = serialport.read()
		logdebug('Byte: ' + str(ByteToHex(byte)))
		
		if byte:
			message = byte + readbytes( ord(byte) )
			logdebug('Message: ' + str(ByteToHex(message)))
			
			if ByteToHex(message[0]) <> "00":
			
				# Verify length
				logdebug('Verify length')
				if (len(message) - 1) == ord(message[0]):
				
					logdebug('Length OK')
					if printout_complete == True:
						print "------------------------------------------------"
						print "Received\t\t= " + ByteToHex( message )
						print "Date/Time\t\t= " + timestamp
						print "Packet Length\t\t= " + ByteToHex( message[0] )
					
					logdebug('Decode packet')
					try:
						decodePacket( message )
					except KeyError:
						logdebug('Error: unrecognizable packet')
						print "Error: unrecognizable packet"

					rawcmd = ByteToHex ( message )
					rawcmd = rawcmd.replace(' ', '')

					return rawcmd
				
				else:
				
					if printout_complete == True:
						logdebug('Incoming packet not valid')
						print "------------------------------------------------"
						print "Received\t\t= " + ByteToHex( message )
						print "Incoming packet not valid, waiting for next..."
				
	except OSError, e:
		logdebug('Error in message: ' + str(ByteToHex(message)))
		logdebug('Traceback: ' + traceback.print_exc())
		print "------------------------------------------------"
		print "Received\t\t= " + ByteToHex( message )
		traceback.print_exc()

# ----------------------------------------------------------------------------
# READ ITEM FROM THE CONFIGURATION FILE
# ----------------------------------------------------------------------------

def read_config( configFile, configItem):
 
 	logdebug('Open configuration file')
 	logdebug('File: ' + configFile)
	
	if os.path.exists( configFile ):

		#open the xml file for reading:
		f = open( configFile,'r')
		data = f.read()
		f.close()
	
		# xml parse file data
 		logdebug('Parse config XML data')
		try:
			dom = parseString(data)
		except:
			print "Error: problem in the config.xml file, cannot process it"
			logdebug('Error in config.xml file')
			
		# Get config item
	 	logdebug('Get the configuration item: ' + configItem)
		
		try:
			xmlTag = dom.getElementsByTagName( configItem )[0].toxml()
			logdebug('Found: ' + xmlTag)
			xmlData = xmlTag.replace('<' + configItem + '>','').replace('</' + configItem + '>','')
			logdebug('--> ' + xmlData)
		except:
			logdebug('The item tag not found in the config file')
			xmlData = ""
			
 		logdebug('Return')
 		
 	else:
 		logdebug('Config file does not exists')
 		
	return xmlData

# ----------------------------------------------------------------------------
# TRIGGER
# ----------------------------------------------------------------------------

def read_trigger():
 
	xmldoc = minidom.parse('trigger.xml')
	root = xmldoc.documentElement

	triggers = root.getElementsByTagName('trigger')

	triggerlist = []
	x = 1
	
	for trigger in triggers:
		message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
		action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
 		triggerlist = [ message, action ]
 		return triggerlist
 	
# ----------------------------------------------------------------------------
# RESPONSES
# ----------------------------------------------------------------------------

rfx_cmnd = {"00":"Reset the receiver/transceiver. No answer is transmitted!",
			"01":"Not used.",
			"02":"Get Status, return firmware versions and configuration of the interface.",
			"03":"Set mode msg1-msg5, return firmware versions and configuration of the interface.",
			"04":"Enable all receiving modes of the receiver/transceiver.",
			"05":"Enable reporting of undecoded packets.",
			"06":"Save receiving modes of the receiver/transceiver in non-volatile memory.",
			"07":"Not used.",
			"08":"T1 - for internal use by RFXCOM",
			"09":"T2 - for internal use by RFXCOM"}

rfx_packettype = {
				"00":"Interface Control",
				"01":"Interface Message",
				"02":"Receiver/Transmitter Message",
				"03":"Undecoded RF Message",
				"10":"Lighting1",
				"11":"Lighting2",
				"12":"Lighting3",
				"13":"Lighting4",
				"14":"Lighting5",
				"15":"Lighting6",
				"18":"Curtain1",
				"19":"Blinds1",
				"20":"Security1",
				"28":"Camera1",
				"30":"Remote control and IR",
				"40":"Thermostat1",
				"41":"Thermostat2 (Receive not implemented)",
				"42":"Thermostat3",
				"50":"Temperature sensors",
				"51":"Humidity sensors",
				"52":"Temperature and humidity sensors",
				"53":"Barometric sensors",
				"54":"Temperature, humidity and barometric sensors",
				"55":"Rain sensors",
				"56":"Wind sensors",
				"57":"UV sensors",
				"58":"Date/Time sensors",
				"59":"Current sensors",
				"5A":"Energy usage sensors",
				"5B":"Gas usage sensors",
				"5C":"Water usage sensors",
				"5D":"Weighting scale",
				"70":"RFXSensor",
				"71":"RFXMeter",
				"72":"FS20"}

rfx_subtype_01 = {"00":"Response on a mode command"}

rfx_subtype_01_msg1 = {"50":"310MHz",
						"51":"315MHz",
						"52":"433.92MHz (Receiver only)",
						"53":"433.92MHz (Transceiver)",
						"55":"868.00MHz",
						"56":"868.00MHz FSK",
						"57":"868.30MHz",
						"58":"868.30MHz FSK",
						"59":"868.35MHz",
						"5A":"868.35MHz FSK",
						"5B":"868.95MHz"}

rfx_subtype_01_msg3 = {"128":"Display of undecoded packets",
						"64":"RFU6",
						"32":"RFU5",
						"16":"RFU4",
						"8":"RFU3",
						"4":"FineOffset / Viking (433.92)",
						"2":"Rubicson (433.92)",
						"1":"AE (433.92)"}
						
rfx_subtype_01_msg4 = {"128":"BlindsT1/T2/T3 (433.92)",
						"64":"BlindsT0 (433.92)",
						"32":"ProGuard (868.35 FSK)",
						"16":"FS20 (868.35)",
						"8":"La Crosse (433.92/868.30)",
						"4":"Hideki/UPM (433.92)",
						"2":"AD (433.92)",
						"1":"Mertik (433.92)"}
						
rfx_subtype_01_msg5 = {"128":"Visonic (315/868.95)",
						"64":"ATI (433.92)",
						"32":"Oregon Scientific (433.92)",
						"16":"Meiantech (433.92)",
						"8":"HomeEasy EU (433.92)",
						"4":"AC (433.92)",
						"2":"ARC (433.92)",
						"1":"X10 (310/433.92)"}

rfx_subtype_02 = {"00":"Error, receiver did not lock",
					"01":"Transmitter response"}
					
rfx_subtype_02_msg1 = {"00":"ACK, transmit OK",
						"01":"ACK, but transmit started after 3 seconds delay anyway with RF receive data",
						"02":"NAK, transmitter did not lock on the requested transmit frequency",
						"03":"NAK, AC address zero in id1-id4 not allowed"}

rfx_subtype_03 = {"00":"AC",
					"01":"ARC",
					"02":"ATI",
					"03":"Hideki",
					"04":"LaCrosse",
					"05":"AD",
					"06":"Mertik",
					"07":"Oregon 1",
					"08":"Oregon 2",
					"09":"Oregon 3",
					"0A":"Proguard",
					"0B":"Visionic",
					"0C":"NEC",
					"0D":"FS20",
					"0E":"Reserved",
					"0F":"Blinds",
					"10":"Rubicson",
					"11":"AE",
					"12":"Fineoffset"}

rfx_subtype_10 = {"00":"X10 Lightning",
					"01":"ARC",
					"02":"ELRO AB400D (Flamingo)",
					"03":"Waveman",
					"04":"Chacon EMW200",
					"05":"IMPULS",
					"06":"RisingSun",
					"07":"Philips SBC"}

rfx_subtype_10_cmnd = {"00":"Off",
						"01":"On",
						"02":"Dim",
						"03":"Bright",
						"04":"All/Group Off",
						"05":"All/Group On",
						"07":"Chime",
						"ff":"Illegal cmnd received"}

rfx_subtype_11 = {"00":"AC",
					"01":"HomeEasy EU",
					"02":"Anslut"}
					
rfx_subtype_11_cmnd = {"00":"Off",
						"01":"On",
						"02":"Set level",
						"03":"Group Off",
						"04":"Group On",
						"05":"Set Group Level"}

rfx_subtype_12 = {"00":"Ikea Koppla"}

rfx_subtype_13 = {"00":"PT2262"}

rfx_subtype_14 = {"00":"LightwaveRF, Siemens",
					"01":"EMW100 GAO/Everflourish"}
					
rfx_subtype_15 = {"00":"Blyss"}

rfx_subtype_15_groupcode = {"41":"A",
							"42":"B",
							"43":"C",
							"44":"D",
							"45":"E",
							"46":"F",
							"47":"G",
							"48":"H"}

rfx_subtype_15_cmnd = {"00":"On",
						"01":"Off",
						"02":"group On",
						"03":"group Off"}

rfx_subtype_18 = {"00":"Harrison Curtain"}

rfx_subtype_19 = {"00":"BlindsT0 / Rollertrol, Hasta new",
					"01":"BlindsT1 / Hasta old",
					"02":"BlindsT2 / A-OK RF01",
					"03":"BlindsT3 / A-OK AC114"}

rfx_subtype_20 = {"00":"X10 security door/window sensor",
					"01":"X10 security motion sensor",
					"02":"X10 security remote (no alive packets)",
					"03":"KD101 (no alive packets)",
					"04":"Visonic PowerCode door/window sensor - Primary contact (with alive packets)",
					"05":"Visonic PowerCode motion sensor (with alive packets)",
					"06":"Visonic CodeSecure (no alive packets)",
					"07":"Visonic PowerCode door/window sensor - auxiliary contact (no alive packets)",
					"08":"Meiantech"}

rfx_subtype_20_status = {"00":"Normal",
						"01":"Normal delayed",
						"02":"Alarm",
						"03":"Alarm delayed",
						"04":"Motion",
						"05":"No motion",
						"06":"Panic",
						"07":"End panic",
						"08":"IR",
						"09":"Arm away",
						"0A":"Arm away delayed",
						"0B":"Arm home",
						"0C":"Arm home delayed",
						"0D":"Disarm",
						"10":"Light 1 off",
						"11":"Light 1 on",
						"12":"Light 2 off",
						"13":"Light 2 on",
						"14":"Dark detected",
						"15":"Light detected",
						"16":"Batlow (SD18, CO18)",
						"17":"Pair (KD101)",
						"80":"Normal + tamper",
						"81":"Normal delayed + tamper",
						"82":"Alarm + tamper",
						"83":"Normal delayed + tamper",
						"84":"Motion + tamper",
						"85":"No motion + tamper"}

rfx_subtype_28 = {"00":"X10 Ninja"}

rfx_subtype_30 = {"00":"ATI Remote Wonder",
					"01":"ATI Remote Wonder Plus",
					"02":"Medion Remote",
					"03":"X10 PC Remote",
					"04":"ATI Remote Wonder II (receive only)"}

rfx_subtype_40 = {"00":"Digimax",
					"01":"Digimax with short format (no set point)"}

# 0x41 receive not implemented in RFX
rfx_subtype_41 = {"00":"HE105",
					"01":"RTS10"}

rfx_subtype_42 = {"00":"Mertik G6R-H4T1",
					"01":"Mertik G6R-H4TB"}

rfx_subtype_50 = {"01":"THR128/138, THC138",
					"02":"THC238/268,THN132,THWR288,THRN122,THN122,AW129/131",
					"03":"THWR800",
					"04":"RTHN318",
					"05":"La Crosse TX3, TX4, TX17",
					"06":"TS15C",
					"07":"Viking 02811",
					"08":"La Crosse WS2300",
					"09":"RUBiCSON",
					"0A":"TFA 30.3133"}

rfx_subtype_51 = {"01":"LaCrosse TX3",
					"02":"LaCrosse WS2300"}

rfx_subtype_52 = {"01":"THGN122/123, THGN132, THGR122/228/238/268",
					"02":"THGR810, THGN800",
					"03":"RTGR328",
					"04":"THGR328",
					"05":"WTGR800",
					"06":"THGR918, THGRN228, THGN50",
					"07":"TFA TS34C, Cresta",
					"08":"WT260,WT260H,WT440H,WT450,WT450H",
					"09":"Viking 02035, 02038"}

rfx_subtype_53 = {"01":"Reserved for future use"}

rfx_subtype_54 = {"01":"BTHR918",
					"02":"BTHR918N, BTHR968"}
					
rfx_subtype_55 = {"01":"RGR126/682/918",
					"02":"PCR800",
					"03":"TFA",
					"04":"UPM RG700",
					"05":"WS2300"}
					
rfx_subtype_56 = {"01":"WTGR800",
					"02":"WGR800",
					"03":"STR918, WGR918",
					"04":"TFA (WIND4)",
					"05":"UPM WDS500",
					"06":"WS2300"}

rfx_subtype_57 = {"01":"UVN128, UV138",
					"02":"UVN800",
					"03":"TFA"}
					
rfx_subtype_58 = {"01":"RTGR328N"}

rfx_subtype_59 = {"01":"CM113, Electrisave"}

rfx_subtype_5A = {"01":"CM119/160",
					"02":"CM180"}

rfx_subtype_5B = {"01":"CM180i"}

rfx_subtype_5D = {"01":"BWR101/102",
					"02":"GR101"}
					
rfx_subtype_70 = {"00":"RFXSensor temperature",
					"01":"RFXSensor A/S",
					"02":"RFXSensor voltage",
					"03":"RFXSensor message"}
					
rfx_subtype_71 = {"00":"Normal data packet",
					"01":"New interval time set",
					"02":"Calibrate value in <count> in usec",
					"03":"New address set",
					"04":"Counter value reset within 5 seconds",
					"0B":"Counter value reset executed",
					"0C":"Set interval mode within 5 seconds",
					"0D":"Calibration mode within 5 seconds",
					"0E":"Set address mode within 5 seconds",
					"0F":"Identification packet"}
					
rfx_subtype_72 = {"00":"FS20",
					"01":"FHT8V valve",
					"02":"FHT80 door/window sensor"}
	
# ----------------------------------------------------------------------------
# RFX COMMANDS
# ----------------------------------------------------------------------------

rfx_reset="0d00000000000000000000000000"
rfx_status="0d00000002000000000000000000"
rfx_undecoded="0d00000005000000000000000000"
rfx_save="0d00000006000000000000000000"

# ----------------------------------------------------------------------------
# Printout types

printout_complete = True
printout_csv = False

# Check current Python version
if sys.hexversion < 0x02060000:
	print "Error: Your Python need to be 2.6 or newer, please upgrade."
	exit()

# ----------------------------------------------------------------------------
# PARSE COMMAND LINE ARGUMENT
# ----------------------------------------------------------------------------

logdebug("Parse command line")

parser = OptionParser()
parser.add_option("-d", "--device", action="store", type="string", dest="device", help="The serial device of the RFXCOM, example /dev/ttyUSB0")
parser.add_option("-a", "--action", action="store", type="string", dest="action", help="Specify which action: LISTEN (default), STATUS, SEND, BSEND")
parser.add_option("-o", "--config", action="store", type="string", dest="config", help="Specify the configuration file")
parser.add_option("-x", "--simulate", action="store", type="string", dest="simulate", help="Simulate one incoming data message")
parser.add_option("-r", "--rawcmd", action="store", type="string", dest="rawcmd", help="Send raw message (need action SEND)")
parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, help="Output data in CSV format")
parser.add_option("-m", "--mysql", action="store_true", dest="mysql", default=False, help="Insert data to MySQL database")
parser.add_option("-s", "--sqlite", action="store_true", dest="sqlite", default=False, help="Insert data to SQLite database")
parser.add_option("-g", "--graphite", action="store_true", dest="graphite", default=False, help="Send data to graphite server")
parser.add_option("-z", "--daemonize", action="store_true", dest="daemon", default=False, help="Daemonize RFXCMD")
parser.add_option("-p", "--pidfile", action="store", type="string", dest="pidfile", help="PID File location and name")

(options, args) = parser.parse_args()

if options.csv:
	logdebug("Option: CSV chosen")
	printout_complete = False
	printout_csv = True

if options.mysql:
	logdebug("Option: MySQL chosen")
	printout_complete = False
	printout_csv = False

if options.sqlite:
	logdebug("Option: SqLite chosen")
	printout_complete = False
	printout_csv = False

if printout_complete == True:
	if not options.daemon:
		print sw_name + " version " + sw_version

if options.config:
	configFile = options.config
else:
	configFile = "config.xml"

logdebug("Configfile: " + configFile)

# Deamon
if options.daemon:

	logdebug("Check PID file")
	if options.pidfile:
		config.pidfile = options.pidfile
		config.createpid = True

		logdebug("PID file '" + config.pidfile + "'")
		if os.path.exists(config.pidfile):
			print("PID file '" + config.pidfile + "' already exists. Exiting.")
			logdebug("PID file '" + config.pidfile + "' already exists. Exiting.")
			sys.exit(1)
		else:
			logdebug("PID file does not exists")

	else:
		print("You need to set the --pidfile parameter at the startup")
		logdebug("Command argument --pidfile missing")
		sys.exit(1)

	logdebug("Check platform")
	if sys.platform == 'win32':
		print "Daemonize not supported under Windows."
		logdebug("Daemonize not supported under Windows.")
		sys.exit()
	else:
		logdebug("Platform: " + sys.platform)
		try:
			logdebug("Write PID file")
			file(config.pidfile, 'w').write("pid\n")
		except IOError, e:
			logdebug("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))
			raise SystemExit("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))

		logdebug("Deactivate screen printouts")
		printout_complete = False

		logdebug("Start daemon")
		daemonize()

# MySQL
if options.mysql == True:
	try:
		logdebug("Import MySQLdb")
		import MySQLdb
	except ImportError:
		print "Error: You need to install MySQL extension for Python"
		logdebug("Error: Could not find MySQL extension for Python")
		sys.exit(1)

# SqLite
if options.sqlite == True:
	try:
		import sqlite3
	except ImportError:
		print "Error: You need to install SQLite extension for Python"
		sys.exit(1)

if options.action == "send" or options.action == "bsend":
	rfxcmd_rawcmd = options.rawcmd
	if not rfxcmd_rawcmd:
		print "Error: You need to specify message to send with -r <rawcmd>"
		sys.exit(1)

if options.action:
	rfxcmd_action = options.action.lower()
	if not (rfxcmd_action == "listen" or 
		rfxcmd_action == "send" or
		rfxcmd_action == "bsend" or
		rfxcmd_action == "status"):
		parser.error('Invalid action')
else:
	rfxcmd_action = "listen"

logdebug("Action chosen: " + rfxcmd_action)

# ----------------------------------------------------------------------------
# READ CONFIGURATION FILE
# ----------------------------------------------------------------------------

if os.path.exists( configFile ):

	# RFX configuration
	if ( read_config( configFile, "undecoded") == "yes"):
		config.undecoded = True
	else:
		config.undecoded = False

	# MySQL configuration
	config.mysql_server = read_config( configFile, "mysql_server")
	config.mysql_database = read_config( configFile, "mysql_database")
	config.mysql_username = read_config( configFile, "mysql_username")
	config.mysql_password = read_config( configFile, "mysql_password")
	
	if ( read_config( configFile, "trigger") == "yes"):
		config.trigger = True
	else:
		config.trigger = False

	config.triggerfile = read_config( configFile, "triggerfile")	

	# SQLite configuration
	config.sqlite_server = read_config( configFile, "sqlite_server")
	config.sqlite_database = read_config( configFile, "sqlite_database")
	config.sqlite_username = read_config( configFile, "sqlite_username")
	config.sqlite_password = read_config( configFile, "sqlite_password")
	
	# Configuration for Graphite server
	config.graphite_server = read_config( configFile, "graphite_server")
	config.graphite_port = read_config( configFile, "graphite_port")

else:

	# config file not found, set default values
	print "Error: Configuration file not found (" + configFile + ")"

	logerror('Error: Configuration file not found (' + configFile + ')')

	config.undecoded = False
	
	config.mysql_server = ""
	config.mysql_database = ""
	config.mysql_username = ""
	config.mysql_password = ""

	config.trigger = False

	config.sqlite_server = ""
	config.sqlite_database = ""
	config.sqlite_username = ""
	config.sqlite_password = ""
	
	config.graphite_server = ""
	config.graphite_port = ""

# ----------------------------------------------------------------------------
# SIMULATE
# ----------------------------------------------------------------------------

if options.simulate:

	# If trigger is activated in config, then read the triggerfile
	if config.trigger:
		xmldoc = minidom.parse( config.triggerfile )
		root = xmldoc.documentElement

		triggers = root.getElementsByTagName('trigger')

		triggerlist = []
	
		for trigger in triggers:
			message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
			action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
 			triggerlist = [ message, action ]

	indata = options.simulate
	print "------------------------------------------------"
	
	# remove all spaces
	for x in string.whitespace:
		indata = indata.replace(x,"")
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	
	print "Received\t\t= " + indata
	print "Date/Time\t\t= " + timestamp
	
	# Verify that the incoming value is hex
	try:
		hexval = int(indata, 16)
	except:
		print "Error: the input data is invalid hex value"
		exit()
	
	# cut into hex chunks
	try:
		message = indata.decode("hex")
	except:
		print "Error: the input data is not valid"
		exit()
	
	# decode it
	try:
		decodePacket( message )
	except KeyError:
		print "Error: unrecognizable packet"

	if config.trigger:
		if message:
			for trigger in triggers:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					return_code = subprocess.call(action, shell=True)
	
	logdebug('Exit 0')
	sys.exit(0)

# ----------------------------------------------------------------------------
# OPEN SERIAL CONNECTION
# ----------------------------------------------------------------------------

if options.device:
	device=options.device
else:
	logerror('Device name missing')
	parser.error('Device name missing')

# Open serial port
try:  
	serialport = serial.Serial(device, 38400, timeout=9)
except:  
	print "Error: Failed to connect on " + device
	logdebug('sys.exit(1)')
	sys.exit(1)

already_open = serialport.isOpen()
if not already_open:
	serialport.open()

# ----------------------------------------------------------------------------
# LISTEN TO RFX, EXIT WITH CTRL+C
# ----------------------------------------------------------------------------

if rfxcmd_action == "listen":

	logdebug('Action: Listen')

	# If trigger is activated in config, then read the triggerfile
	if config.trigger:
		xmldoc = minidom.parse( config.triggerfile )
		root = xmldoc.documentElement

		triggers = root.getElementsByTagName('trigger')

		triggerlist = []
	
		for trigger in triggers:
			message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
			action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
 			triggerlist = [ message, action ]
			
	# Flush buffer
	logdebug('Serialport flush output')
	serialport.flushOutput()
	logdebug('Serialport flush input')
	serialport.flushInput()

	# Send RESET
	logdebug('Send rfx_reset (' + rfx_reset + ')')
	serialport.write( rfx_reset.decode('hex') )
	logdebug('Sleep 1 sec')
	time.sleep(1)

	# Flush buffer
	logdebug('Serialport flush output')
	serialport.flushOutput()
	logdebug('Serialport flush input')
	serialport.flushInput()

	if config.undecoded:
		logdebug('Send rfx_undecoded (' + rfx_undecoded + ')')
		send_rfx( rfx_undecoded.decode('hex') )
		logdebug('Sleep 1 sec')
		time.sleep(1)
		logdebug('Read_rfx')
		read_rfx()
		
	# Send STATUS
	logdebug('Send rfx_status (' + rfx_status + ')')
	serialport.write( rfx_status.decode('hex') )
	logdebug('Sleep 1 sec')
	time.sleep(1)

	try:
		while 1:
			rawcmd = read_rfx()
			logdebug('Received: ' + str(rawcmd))

			if config.trigger:
				if rawcmd:
					for trigger in triggers:
						message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
						action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
						if re.match(message, rawcmd):
							return_code = subprocess.call(action, shell=True)

	except KeyboardInterrupt:
		logdebug('Received keyboard interrupt')
		print "\nExit..."
		pass

# ----------------------------------------------------------------------------
# STATUS
# ----------------------------------------------------------------------------

if rfxcmd_action == "status":

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	# Send RESET
	serialport.write( rfx_reset.decode('hex') )
	time.sleep(1)

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	if config.undecoded:
		send_rfx( rfx_undecoded.decode('hex') )
		time.sleep(1)
		read_rfx()
		
	# Send STATUS
	send_rfx( rfx_status.decode('hex') )
	time.sleep(1)
	read_rfx()

# ----------------------------------------------------------------------------
# SEND
# ----------------------------------------------------------------------------

if rfxcmd_action == "send":

	# Remove any whitespaces	
	rfxcmd_rawcmd = rfxcmd_rawcmd.replace(' ', '')
	
	# Test the string if it is hex format
	try:
		int(rfxcmd_rawcmd,16)
	except ValueError:
		print "Error: invalid rawcmd, not hex format"
		sys.exit(1)		
	
	# Check that first byte is not 00
	if ByteToHex(rfxcmd_rawcmd.decode('hex')[0]) == "00":
		print "Error: invalid rawcmd, first byte is zero"
		sys.exit(1)
	
	# Check if string is the length that it reports to be
	cmd_len = int( ByteToHex(rfxcmd_rawcmd.decode('hex')[0]),16 )
	if not len(rfxcmd_rawcmd.decode('hex')) == (cmd_len + 1):
		print "Error: invalid rawcmd, invalid length"
		sys.exit(1)

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	# Send RESET
	serialport.write( rfx_reset.decode('hex') )
	time.sleep(1)

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	if config.undecoded:
		send_rfx( rfx_undecoded.decode('hex') )
		time.sleep(1)
		read_rfx()
		
	if rfxcmd_rawcmd:
		timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
		if printout_complete == True:
			print "------------------------------------------------"
			print "Send\t\t\t= " + ByteToHex( rfxcmd_rawcmd.decode('hex') )
			print "Date/Time\t\t= " + timestamp
			print "Packet Length\t\t= " + ByteToHex(rfxcmd_rawcmd.decode('hex')[0])
			try:
				decodePacket( rfxcmd_rawcmd.decode('hex') )
			except KeyError:
				print "Error: unrecognizable packet"

		serialport.write( rfxcmd_rawcmd.decode('hex') )
		time.sleep(1)
		read_rfx()

# ----------------------------------------------------------------------------
# BSEND
# ----------------------------------------------------------------------------

if rfxcmd_action == "bsend":
	
	logdebug('Action: bsend')
	
	# Remove any whitespaces
	rfxcmd_rawcmd = rfxcmd_rawcmd.replace(' ', '')
	logdebug('rawcmd: ' + rfxcmd_rawcmd)
	
	# Test the string if it is hex format
	try:
		int(rfxcmd_rawcmd,16)
	except ValueError:
		print "Error: invalid rawcmd, not hex format"
		sys.exit(1)		
	
	# Check that first byte is not 00
	if ByteToHex(rfxcmd_rawcmd.decode('hex')[0]) == "00":
		print "Error: invalid rawcmd, first byte is zero"
		sys.exit(1)
	
	# Check if string is the length that it reports to be
	cmd_len = int( ByteToHex(rfxcmd_rawcmd.decode('hex')[0]),16 )
	if not len(rfxcmd_rawcmd.decode('hex')) == (cmd_len + 1):
		print "Error: invalid rawcmd, invalid length"
		sys.exit(1)

	if rfxcmd_rawcmd:
		serialport.write( rfxcmd_rawcmd.decode('hex') )
	
# ----------------------------------------------------------------------------
# CLOSE SERIAL CONNECTION
# ----------------------------------------------------------------------------

logdebug('Close serial port')
try:
	serialport.close()
except:
	logdebug("Failed to close the serial port '" + device + "'")
	print "Error: Failed to close the port " + device
	logdebug("Exit 1")
	sys.exit(1)
	
logdebug("Exit 0")
sys.exit(0)
