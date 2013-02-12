#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#	
#	RFXCMD.PY
#	
#	Copyright (C) 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
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
#	$Rev$
#	$Date$
#
#	NOTES
#	
#	RFXCOM is a Trademark of RFSmartLink.
#
# ------------------------------------------------------------------------------
#
#                          Protocol License Agreement                      
#                                                                    
# The RFXtrx protocols are owned by RFXCOM, and are protected under applicable
# copyright laws.
#
# ==============================================================================
# It is only allowed to use this protocol or any part of it for RFXCOM products
# ==============================================================================
#
# The above Protocol License Agreement and the permission notice shall be 
# included in all software using the RFXtrx protocols.
#
# Any use in violation of the foregoing restrictions may subject the user to 
# criminal sanctions under applicable laws, as well as to civil liability for 
# the breach of the terms and conditions of this license.
#
# ------------------------------------------------------------------------------

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2013, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "0.3 (" + filter(str.isdigit, "$Rev$") + ")"
__maintainer__ = "Sebastian Sjoholm"
__email__ = "sebastian.sjoholm@gmail.com"
__status__ = "Development"
__date__ = "$Date$"

# Default modules
import pdb
import string
import sys
import os
import time
import datetime
import binascii
import traceback
import subprocess
import re
import logging
import signal
from xml.dom.minidom import parseString
import xml.dom.minidom as minidom
from optparse import OptionParser
import socket

# 3rd party modules
# These might not be needed, depended on usage

# SQLite
try:
	import sqlite3
except ImportError:
	pass

# MySQL
try:
	import MySQLdb
except ImportError:
	pass

# Serial
try:
	import serial
except ImportError:
	pass

# XPLLib
try:
	import xpl
except ImportError:
	pass

# ------------------------------------------------------------------------------
# VARIABLE CLASSS
# ------------------------------------------------------------------------------

class config_data:
	def __init__(
		self, 
		undecoded = False,
		mysql_server = '',
		mysql_database = '',
		mysql_username = "",
		mysql_password = "",
		trigger = False,
		triggerfile = "",
		sqlite_database = "",
		sqlite_table = "",
		loglevel = "info",
		graphite_server = "",
		graphite_port = "",
		program_path = "",
		xplhost = ""
		):
        
		self.undecoded = undecoded
		self.mysql_server = mysql_server
		self.mysql_database = mysql_database
		self.mysql_username = mysql_username
		self.mysql_password = mysql_password
		self.trigger = trigger
		self.triggerfile = triggerfile
		self.sqlite_database = sqlite_database
		self.sqlite_table = sqlite_table
		self.loglevel = loglevel
		self.graphite_server = graphite_server
		self.graphite_port = graphite_port
		self.program_path = program_path
		self.xplhost = xplhost

class cmdarg_data:
	def __init__(
		self,
		configfile = "",
		action = "",
		rawcmd = "",
		device = "",
		createpid = False,
		pidfile = "",
		printout_complete = True,
		printout_csv = False,
		mysql = False,
		sqlite = False,
		graphite = False,
		xpl = False
		):

		self.configfile = configfile
		self.action = action
		self.rawcmd = rawcmd
		self.device = device
		self.createpid = createpid
		self.pidfile = pidfile
		self.printout_complete = printout_complete
		self.printout_csv = printout_csv
		self.mysql = mysql
		self.sqlite = sqlite
		self.graphite = graphite
		self.xpl = xpl

class rfx_data(dict):

	rfx_cmnd = {
				"00":"Reset the receiver/transceiver. No answer is transmitted!",
				"01":"Not used.",
				"02":"Get Status, return firmware versions and configuration of the interface.",
				"03":"Set mode msg1-msg5, return firmware versions and configuration of the interface.",
				"04":"Enable all receiving modes of the receiver/transceiver.",
				"05":"Enable reporting of undecoded packets.",
				"06":"Save receiving modes of the receiver/transceiver in non-volatile memory.",
				"07":"Not used.",
				"08":"T1 - for internal use by RFXCOM",
				"09":"T2 - for internal use by RFXCOM"
				}

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
				"72":"FS20"
				}

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

	rfx_subtype_10_housecode = {"41":"A",
								"42":"B",
								"43":"C",
								"44":"D",
								"45":"E",
								"46":"F",
								"47":"G",
								"48":"H",
								"49":"I",
								"4A":"J",
								"4B":"K",
								"4C":"L",
								"4D":"M",
								"4E":"N",
								"4F":"O",
								"50":"P"}

	rfx_subtype_10_cmnd = {"00":"Off",
							"01":"On",
							"02":"Dim",
							"03":"Bright",
							"04":"All/Group Off",
							"05":"All/Group On",
							"07":"Chime",
							"FF":"Illegal cmnd received"}

	rfx_subtype_11 = {"00":"AC",
						"01":"HomeEasy EU",
						"02":"Anslut"}
					
	rfx_subtype_11_cmnd = {"00":"Off",
							"01":"On",
							"02":"Set level",
							"03":"Group Off",
							"04":"Group On",
							"05":"Set Group Level"}

	rfx_subtype_11_dimlevel = {"00":"0",
								"01":"6",
								"02":"12",
								"03":"18",
								"04":"24",
								"05":"30",
								"06":"36",
								"07":"42",
								"08":"48",
								"09":"54",
								"0A":"60",
								"0B":"66",
								"0C":"72",
								"0D":"78",
								"0E":"84",
								"0F":"100"}

	rfx_subtype_12 = {"00":"Ikea Koppla"}

	rfx_subtype_12_cmnd = {"00":"Bright",
							"08":"Dim",
							"10":"On",
							"11":"Level 1",
							"12":"Level 2",
							"13":"Level 3",
							"14":"Level 4",
							"15":"Level 5",
							"16":"Level 6",
							"17":"Level 7",
							"18":"Level 8",
							"19":"Level 9",
							"1A":"Off",
							"1C":"Program"}

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

	rfx_subtype_30_atiremotewonder = {"00":"A",
									"01":"B",
									"02":"Power",
									"03":"TV",
									"04":"DVD",
									"05":"?",
									"06":"Guide",
									"07":"Drag",
									"08":"VOL+",
									"09":"VOL-",
									"0A":"MUTE",
									"0B":"CHAN+",
									"0C":"CHAN-",
									"0D":"1",
									"0E":"2",
									"0F":"3",
									"10":"4",
									"11":"5",
									"12":"6",
									"13":"7",
									"14":"8",
									"15":"9",
									"16":"txt",
									"17":"0",
									"18":"Snapshot ESQ",
									"19":"C",
									"1A":"^",
									"1B":"D",
									"1C":"TV/RADIO",
									"1D":"<",
									"1E":"OK",
									"1F":">",
									"20":"<-",
									"21":"E",
									"22":"v",
									"23":"F",
									"24":"Rewind",
									"25":"Play",
									"26":"Fast forward",
									"27":"Record",
									"28":"Stop",
									"29":"Pause",
									"2C":"TV",
									"2D":"VCR",
									"2E":"RADIO",
									"2F":"TV Preview",
									"30":"Channel list",
									"31":"Video Desktop",
									"32":"red",
									"33":"green",
									"34":"yellow",
									"35":"blue",
									"36":"rename TAB",
									"37":"Acquire image",
									"38":"edit image",
									"39":"Full Screen",
									"3A":"DVD Audio",
									"70":"Cursor-left",
									"71":"Cursor-right",
									"72":"Cursor-up",
									"73":"Cursor-down",
									"74":"Cursor-up-left",
									"75":"Cursor-up-right",
									"76":"Cursor-down-right",
									"77":"Cursor-down-left",
									"78":"V",
									"79":"V-End",
									"7C":"X",
									"7D":"X-End"}

	rfx_subtype_30_medion = {"00":"Mute",
							"01":"B",
							"02":"Power",
							"03":"TV",
							"04":"DVD",
							"05":"Photo",
							"06":"Music",
							"07":"Drag",
							"08":"VOL-",
							"09":"VOL+",
							"0A":"MUTE",
							"0B":"CHAN+",
							"0C":"CHAN-",
							"0D":"1",
							"0E":"2",
							"0F":"3",
							"10":"4",
							"11":"5",
							"12":"6",
							"13":"7",
							"14":"8",
							"15":"9",
							"16":"txt",
							"17":"0",
							"18":"snapshot ESQ",
							"19":"DVD MENU",
							"1A":"^",
							"1B":"Setup",
							"1C":"TV/RADIO",
							"1D":"<",
							"1E":"OK",
							"1F":">",
							"20":"<-",
							"21":"E",
							"22":"v",
							"23":"F",
							"24":"Rewind",
							"25":"Play",
							"26":"Fast forward",
							"27":"Record",
							"28":"Stop",
							"29":"Pause",
							"2C":"TV",
							"2D":"VCR",
							"2E":"RADIO",
							"2F":"TV Preview",
							"30":"Channel List",
							"31":"Video desktop",
							"32":"red",
							"33":"green",
							"34":"yellow",
							"35":"blue",
							"36":"rename TAB",
							"37":"Acquire image",
							"38":"edit image",
							"39":"Full screen",
							"3A":"DVD Audio",
							"70":"Cursor-left",
							"71":"Cursor-right",
							"72":"Cursor-up",
							"73":"Cursor-down",
							"74":"Cursor-up-left",
							"75":"Cursor-up-right",
							"76":"Cursor-down-right",
							"77":"Cursor-down-left",
							"78":"V",
							"79":"V-End",
							"7C":"X",
							"7D":"X-End"}

	rfx_subtype_40 = {"00":"Digimax",
						"01":"Digimax with short format (no set point)"}

	rfx_subtype_40_status = {"0":"No status available",
							"1":"Demand",
							"2":"No demand",
							"3":"Initializing"}

	rfx_subtype_40_mode = {"0":"Heating",
							"1":"Cooling"}

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

	rfx_subtype_51_humstatus = {"00":"Dry",
								"01":"Comfort",
								"02":"Normal",
								"03":"Wet"}

	rfx_subtype_52 = {"01":"THGN122/123, THGN132, THGR122/228/238/268",
						"02":"THGR810, THGN800",
						"03":"RTGR328",
						"04":"THGR328",
						"05":"WTGR800",
						"06":"THGR918, THGRN228, THGN50",
						"07":"TFA TS34C, Cresta",
						"08":"WT260,WT260H,WT440H,WT450,WT450H",
						"09":"Viking 02035, 02038"}

	rfx_subtype_52_humstatus = {"00":"Dry",
								"01":"Comfort",
								"02":"Normal",
								"03":"Wet"}

	rfx_subtype_53 = {"01":"Reserved for future use"}

	rfx_subtype_54 = {"01":"BTHR918",
						"02":"BTHR918N, BTHR968"}

	rfx_subtype_54_humstatus = {"00":"Dry",
								"01":"Comfort",
								"02":"Normal",
								"03":"Wet"}

	rfx_subtype_54_forecast = {"01":"Sunny",
								"02":"Partly cloudy",
								"03":"Cloudy",
								"04":"Rainy"}

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
					
	rfx_subtype_70_msg03 = {"01":"Sensor addresses incremented",
							"02":"Battery low detected",
							"81":"No 1-wire device connected",
							"82":"1-Wire ROM CRC error",
							"83":"1-Wire device connected is not a DS18B20 or DS2438",
							"84":"No end of read signal received from 1-Wire device",
							"85":"1-Wire scratchpad CRC error"}
					
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

	def __getitem__(self, key): return self[key]
	def keys(self): return self.keys()

class rfxcmd_data:
	def __init__(
		self,
		reset = "0d00000000000000000000000000",
		status = "0d00000002000000000000000000",
		undecoded = "0d00000005000000000000000000",
		save = "0d00000006000000000000000000"
		):

		self.reset = reset
		self.status = status
		self.undecoded = undecoded
		self.save = save

class serial_data:
	def __init__(
		self,
		port = None,
		rate = 38400,
		timeout = 9
		):

		self.port = port
		self.rate = rate
		self.timeout = timeout

# ----------------------------------------------------------------------------

def logdebug(text):
	"""
	Create a debug log entry.
	"""
	try:
		logger.debug(text)
	except NameError:
		pass

# ----------------------------------------------------------------------------

def logerror(text):
	"""
	Create an error log entry.
	"""
	try:
		logger.error(text)
	except NameError:
		pass

# ----------------------------------------------------------------------------
# DEAMONIZE
# Credit: George Henze
# ----------------------------------------------------------------------------

def shutdown():
	# clean up PID file after us
	logdebug("Shutdown")

	if cmdarg.createpid:
		logdebug("Removing PID file " + str(config.pidfile))
		os.remove(cmdarg.pidfile)

	if serial_param.port is not None:
		logdebug("Close serial port")
		serial_param.port.close()
		serial_param.port = None

	logdebug("Exit 0")
	sys.stdout.flush()
	os._exit(0)
    
def handler(signum=None, frame=None):
	if type(signum) != type(None):
		logdebug("Signal %i caught, exiting..." % int(signum))
		shutdown()

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

	if cmdarg.createpid == True:
		pid = str(os.getpid())
		logdebug("Writing PID " + pid + " to " + str(cmdarg.pidfile))
		file(cmdarg.pidfile, 'w').write("%s\n" % pid)

# ----------------------------------------------------------------------------

def send_graphite(CARBON_SERVER, CARBON_PORT, lines):
	"""
	Send data to graphite
	Credit: Frédéric Pégé
	"""	
	sock = None
	for res in socket.getaddrinfo(CARBON_SERVER,int(CARBON_PORT), socket.AF_UNSPEC, socket.SOCK_STREAM):
		af, socktype, proto, canonname, sa = res
		try:
			sock = socket.socket(af, socktype, proto)
		except socket.error as msg:
			sock = None
			continue
		try:
			sock.connect(sa)
		except socket.error as msg:
			sock.close()
			sock = None
			continue
		break

	if sock is None:
		print 'could not open socket'
		sys.exit(1)
	
	message = '\n'.join(lines) + '\n' #all lines must end in a newline
	sock.sendall(message)
	sock.close()

# ----------------------------------------------------------------------------

def readbytes(number):
	"""
	Read x amount of bytes from serial port. 
	Credit: Boris Smus http://smus.com
	"""
	buf = ''
	for i in range(number):
		byte = serial_param.port.read()
		buf += byte

	return buf

# ----------------------------------------------------------------------------

def ByteToHex( byteStr ):
	"""
	Convert a byte string to it's hex string representation e.g. for output.
	http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/

	Added str() to byteStr in case input data is in integer
	"""	
	return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()

# ----------------------------------------------------------------------------

def Decimal2Binary(dec_num):
	"""
	Return the binary representation of dec_num
	http://code.activestate.com/recipes/425080-easy-binary2decimal-and-decimal2binary/
	Guyon Mor�e http://gumuz.looze.net/
	"""
	if dec_num == 0: return '0'
	return (Decimal2Binary(dec_num >> 1) + str(dec_num % 2))

# ----------------------------------------------------------------------------

def testBit(int_type, offset):
	"""
	testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
	http://wiki.python.org/moin/BitManipulation
	"""
	mask = 1 << offset
	return(int_type & mask)

# ----------------------------------------------------------------------------

def clearBit(int_type, offset):
	"""
	clearBit() returns an integer with the bit at 'offset' cleared.
	http://wiki.python.org/moin/BitManipulation
	"""
	mask = ~(1 << offset)
	return(int_type & mask)

# ----------------------------------------------------------------------------

def split_len(seq, length):
	"""
	Split string into specified chunks.
	"""
	return [seq[i:i+length] for i in range(0, len(seq), length)]

# ----------------------------------------------------------------------------

def insert_mysql(timestamp, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, 
	data4, data5, data6, data7, data8, data9, data10, data11, data12, data13):
	"""
	Insert data to MySQL.
	"""

	db = None

	try:

		if data13 == 0:
			data13 = "0000-00-00 00:00:00"

		db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
		cursor = db.cursor()
		sql = """
			INSERT INTO rfxcmd (datetime, packettype, subtype, seqnbr, battery, rssi, processed, data1, data2, data3, data4,
				data5, data6, data7, data8, data9, data10, data11, data12, data13)
			VALUES ('%s','%s','%s','%s','%s','%s',0,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')
			""" % (timestamp, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, data4, data5, data6, data7, 
				data8, data9, data10, data11, data12, data13)
		
		cursor.execute(sql)
		db.commit()

	except MySQLdb.Error, e:

		logerror("SqLite error: %d: %s" % (e.args[0], e.args[1]))
		print "MySQL error %d: %s" % (e.args[0], e.args[1])
		sys.exit(1)

	finally:
		if db:
			db.close()

# ----------------------------------------------------------------------------

def insert_sqlite(timestamp, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, 
	data4, data5, data6, data7, data8, data9, data10, data11, data12, data13):
	"""
	Insert data to SqLite.
	"""

	cx = None

	try:

		cx = sqlite3.connect(config.sqlite_database)
		cu = cx.cursor()
		sql = """
			INSERT INTO '%s' (datetime, packettype, subtype, seqnbr, battery, rssi, processed, data1, data2, data3, data4,
				data5, data6, data7, data8, data9, data10, data11, data12, data13)
			VALUES('%s','%s','%s','%s','%s','%s',0,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')
			""" % (config.sqlite_table, timestamp, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, 
				data4, data5, data6, data7, data8, data9, data10, data11, data12, data13)

		cu.executescript(sql)
		cx.commit()
				
	except sqlite3.Error, e:

		if cx:
			cx.rollback()
			
		logerror("SqLite error: %s" % e.args[0])
		print "SqLite error: %s" % e.args[0]
		sys.exit(1)
			
	finally:
		if cx:
			cx.close()

# ----------------------------------------------------------------------------

def decodeTemperature(message_high, message_low):
	"""
	Decode temperature bytes.
	"""
	temp_high = ByteToHex(message_high)
	temp_low = ByteToHex(message_low)
	polarity = testBit(int(temp_high,16),7)
		
	if polarity == 128:
		polarity_sign = "-"
	else:
		polarity_sign = ""
			
	temp_high = clearBit(int(temp_high,16),7)
	temp_high = temp_high << 8
	temperature = ( temp_high + int(temp_low,16) ) * 0.1
	temperature_str = polarity_sign + str(temperature)

	return temperature_str

# ----------------------------------------------------------------------------

def decodeSignal(message):
	"""
	Decode signal byte.
	"""
	signal = int(ByteToHex(message),16) >> 4
	return signal

# ----------------------------------------------------------------------------

def decodeBattery(message):
	"""
	Decode battery byte.
	"""
	battery = int(ByteToHex(message),16) & 0xf
	return battery

# ----------------------------------------------------------------------------

def decodePacket(message):
	"""
	Decode incoming RFXtrx message.
	"""
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	#timestamp_utc = datetime.datetime.utcnow()
	#unixtime_utc = str(long(time.mktime(timestamp_utc.timetuple())))
	unixtime_utc = int(time.time())

	decoded = False
	db = ""
	
	packettype = ByteToHex(message[1])
	subtype = ByteToHex(message[2])
	seqnbr = ByteToHex(message[3])
	id1 = ByteToHex(message[4])
	
	if len(message) > 5:
		id2 = ByteToHex(message[5])
	
	if cmdarg.printout_complete == True:
		print "Packettype\t\t= " + rfx.rfx_packettype[packettype]

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
		
		if cmdarg.printout_complete == True:
			
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
			print "Response on cmnd\t= " + rfx.rfx_cmnd[data['cmnd']]
		
			# MSG 1
			print "Transceiver type\t= " + rfx.rfx_subtype_01_msg1[data['msg1']]
		
			# MSG 2
			print "Firmware version\t= " + str(int(data['msg2'],16))
			
			if testBit(int(data['msg3'],16),7) == 128:
				print "Display undecoded\t= On"
			else:
				print "Display undecoded\t= Off"

			print "Protocols:"
		
			# MSG 3
			if testBit(int(data['msg3'],16),0) == 1:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['1']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['1']
				
			if testBit(int(data['msg3'],16),1) == 2:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['2']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['2']
				
			if testBit(int(data['msg3'],16),2) == 4:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['4']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['4']
				
			if testBit(int(data['msg3'],16),3) == 8:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['8']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['8']
				
			if testBit(int(data['msg3'],16),4) == 16:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['16']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['16']
				
			if testBit(int(data['msg3'],16),5) == 32:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['32']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['32']
				
			if testBit(int(data['msg3'],16),6) == 64:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg3['64']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg3['64']
		
			# MSG 4
			if testBit(int(data['msg4'],16),0) == 1:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['1']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['1']

			if testBit(int(data['msg4'],16),1) == 2:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['2']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['2']

			if testBit(int(data['msg4'],16),2) == 4:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['4']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['4']

			if testBit(int(data['msg4'],16),3) == 8:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['8']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['8']

			if testBit(int(data['msg4'],16),4) == 16:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['16']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['16']

			if testBit(int(data['msg4'],16),5) == 32:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['32']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['32']

			if testBit(int(data['msg4'],16),6) == 64:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['64']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['64']

			if testBit(int(data['msg4'],16),7) == 128:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg4['128']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg4['128']

			# MSG 5
			if testBit(int(data['msg5'],16),0) == 1:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['1']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['1']

			if testBit(int(data['msg5'],16),1) == 2:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['2']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['2']

			if testBit(int(data['msg5'],16),2) == 4:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['4']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['4']

			if testBit(int(data['msg5'],16),3) == 8:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['8']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['8']

			if testBit(int(data['msg5'],16),4) == 16:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['16']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['16']

			if testBit(int(data['msg5'],16),5) == 32:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['32']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['32']

			if testBit(int(data['msg5'],16),6) == 64:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['64']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['64']

			if testBit(int(data['msg5'],16),7) == 128:
				print "Enabled\t\t\t" + rfx.rfx_subtype_01_msg5['128']
			else:
				print "Disabled\t\t" + rfx.rfx_subtype_01_msg5['128']
		
	# ---------------------------------------
	# 0x02 - Receiver/Transmitter Message
	# ---------------------------------------
	if packettype == '02':
		
		decoded = True
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_02[subtype]
			print "Seqnbr\t\t\t= " + seqnbr

			if subtype == '01':
				print "Message\t\t\t= " + rfx.rfx_subtype_02_msg1[id1]
		
		# CSV
		if cmdarg.printout_csv == True:
			if subtype == '00':
				sys.stdout.write("%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr ) )
			else:
				sys.stdout.write("%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, id1 ) )

		# MYSQL
		if cmdarg.mysql:
			if subtype == '00':
				insert_mysql(timestamp, timeutc, packettype, subtype, seqnbr, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			else:
				insert_mysql(timestamp, timeutc, packettype, subtype, seqnbr, 255, 255, str(id1), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			if subtype == '00':
				insert_sqlite(timestamp, timeutc, packettype, subtype, seqnbr, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			else:
				insert_sqlite(timestamp, timeutc, packettype, subtype, seqnbr, 255, 255, str(id1), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x03 - Undecoded Message
	# ---------------------------------------
	if packettype == '03':
		
		decoded = True
		
		indata = ByteToHex(message)

		# remove all spaces
		for x in string.whitespace:
			indata = indata.replace(x,"")

		indata = indata[4:]

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_03[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Message\t\t\t= " + indata

		# CSV
		if cmdarg.printout_csv == True:
		
			sys.stdout.write("%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, indata ))
		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, indata, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, indata, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x10 Lighting1
	# ---------------------------------------
	if packettype == '10':

		decoded = True
		
		# Housecode
		housecode = rfx.rfx_subtype_10_housecode[ByteToHex(message[4])]

		# Unitcode
		unitcode = int(ByteToHex(message[5]), 16)

		# Command
		command = rfx.rfx_subtype_10_cmnd[ByteToHex(message[6])]

		# Signal		
		signal = decodeSignal(message[7])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_10[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Housecode\t\t= " + housecode
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), housecode, command, str(unitcode) ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, housecode, 0, command, unitcode, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, housecode, 0, command, unitcode, 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x11 Lighting2
	# ---------------------------------------
	if packettype == '11':

		decoded = True
		
		# Id
		sensor_id = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6]) + ByteToHex(message[7])

		# Unitcode
		unitcode = int(ByteToHex(message[8]),16)

		# Command
		command = rfx.rfx_subtype_11_cmnd[ByteToHex(message[9])]

		# Dim level
		try:
			dimlevel = rfx.rfx_subtype_11_dimlevel[ByteToHex(message[10])]
		except Exception, e:
			dimlevel = 255
			logerror("0x11: " + e)

		# Signal
		try:
			signal = decodeSignal(message[11])
		except Exception, e:
			signal = 255
			logerror("0x11: " + e)

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_11[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			print "Dim level\t\t= " + dimlevel + "%"
			print "Signal level\t\t= " + str(signal)
		
		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), sensor_id, command, str(unitcode), dimlevel ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, command, unitcode, int(dimlevel), 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, command, unitcode, int(dimlevel), 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x12 Lighting3
	# ---------------------------------------
	if packettype == '12':

		decoded = True
		
		# System
		system = ByteToHex(message[4])

		# Channel
		if testBit(int(ByteToHex(message[5]),16),0) == 1:
			channel = 1
		elif testBit(int(ByteToHex(message[5]),16),1) == 2:
			channel = 2
		elif testBit(int(ByteToHex(message[5]),16),2) == 4:
			channel = 3
		elif testBit(int(ByteToHex(message[5]),16),3) == 8:
			channel = 4
		elif testBit(int(ByteToHex(message[5]),16),4) == 16:
			channel = 5
		elif testBit(int(ByteToHex(message[5]),16),5) == 32:
			channel = 6
		elif testBit(int(ByteToHex(message[5]),16),6) == 64:
			channel = 7
		elif testBit(int(ByteToHex(message[5]),16),7) == 128:
			channel = 8
		elif testBit(int(ByteToHex(message[6]),16),0) == 1:
			channel = 9
		elif testBit(int(ByteToHex(message[6]),16),1) == 2:
			channel = 10
		else:
			channel = 255

		# Command
		command = rfx.rfx_subtype_12_cmnd[ByteToHex(message[7])]

		# Battery & Signal
		battery = decodeBattery(message[8])
		signal = decodeSignal(message[8])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_12[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "System\t\t\t= " + system
			print "Channel\t\t\t= " + str(channel)
			print "Command\t\t\t= " + command
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV 
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;\n" %(timestamp, packettype, subtype, seqnbr, str(battery), str(signal), str(system), command, str(channel) ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, str(system), 0, command, str(channel), 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, str(system), 0, command, str(channel), 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x13 Lighting4
	# ---------------------------------------
	if packettype == '13':

		decoded = True
		
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_13[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"
			# TODO

	# ---------------------------------------
	# 0x14 Lighting5
	# ---------------------------------------
	if packettype == '14':

		decoded = True
		
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_14[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"
			# TODO

	# ---------------------------------------
	# 0x15 Lighting6
	# Credit: Dimitri Clatot
	# ---------------------------------------
	if packettype == '15':

		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Groupcode
		groupcode = rfx.rfx_subtype_15_groupcode[ByteToHex(message[6])]

		# Unitcode
		unitcode = int(ByteToHex(message[7]),16)

		# Command
		command = rfx.rfx_subtype_15_cmnd[ByteToHex(message[8])]
		command_seqnbr = ByteToHex(message[9])

		# Signal
		signal = decodeSignal(message[11])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_15[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "ID\t\t\t= "  + sensor_id
			print "Groupcode\t\t= " + groupcode
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			print "Command seqnbr\t\t= " + command_seqnbr
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(signal), groupcode, command, str(unitcode), str(command_seqnbr) ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, groupcode, command, unitcode, command_seqnbr, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, groupcode, command, unitcode, command_seqnbr, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x18 Curtain1 (Transmitter only)
	# ---------------------------------------
	if packettype == '18':

		decoded = True
		
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_18[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"

	# ---------------------------------------
	# 0x19 Blinds1
	# ---------------------------------------
	if packettype == '19':

		decoded = True
		
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_19[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"

	# ---------------------------------------
	# 0x20 Security1
	# Credit: Dimitri Clatot
	# ---------------------------------------
	if packettype == '20':

		decoded = True
		
		# Sensor id
		sensor_id = id1 + id2 + ByteToHex(message[6])

		# Status
		status = rfx.rfx_subtype_20_status[ByteToHex(message[7])]

		# Battery & Signal
		signal = decodeSignal(message[8])
		battery = decodeBattery(message[8])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_20[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= "  + sensor_id
			print "Status\t\t\t= " + status
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id, status ) )

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, status, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, status, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x28 Curtain1
	# ---------------------------------------
	if packettype == '28':

		decoded = True
		
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_28[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"

	# ---------------------------------------
	# 0x30 Remote control and IR
	# ---------------------------------------
	if packettype == '30':

		decoded = True

		# Command type
		if subtype == '04':
			if ByteToHex(message[7]) == '00':
				cmndtype = "PC"
			elif ByteToHex(message[7]) == '01':
				cmndtype = "AUX1"
			elif ByteToHex(message[7]) == '02':
				cmndtype = "AUX2"
			elif ByteToHex(message[7]) == '03':
				cmndtype = "AUX3"
			elif ByteToHex(message[7]) == '04':
				cmndtype = "AUX4"
			else:
				cmndtype = "Unknown"

		# Command
		if subtype == '00':
			command = rfx.rfx_subtype_30_atiremotewonder[ByteToHex(message[5])]
		elif subtype == '01':
			command = "Not implemented in RFXCMD"
		elif subtype == '02':
			command = rfx.rfx_subtype_30_medion[ByteToHex(message[5])]
		elif subtype == '03':
			command = "Not implemented in RFXCMD"
		elif subtype == '04':
			command = "Not implemented in RFXCMD"

		# Signal
		if subtype == '00' or subtype == '02' or subtype == '03':
			signal = decodeSignal(message[6])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_30[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + id1
			print "Command\t\t\t= " + command

			if subtype == '04':
				print "Toggle\t\t\t= " + ByteToHex(message[6])

			if subtype == '04':
				print "CommandType\t= " + cmndtype

			print "Signal level\t\t= " + str(signal)

		# CSV 
		if cmdarg.printout_csv == True:
			if subtype == '00' or subtype == '02':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, command))
			elif subtype == '04' or subtype == '01' or subtype == '03':
				command = "Not implemented in RFXCMD"

		# MYSQL
		if cmdarg.mysql:
			if subtype == '00' or subtype == '02':
				insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, id1, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			elif subtype == '04' or subtype == '01' or subtype == '03':
				command = "Not implemented in RFXCMD"

		# SQLITE
		if cmdarg.sqlite:
			if subtype == '00' or subtype == '02':
				insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, id1, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			elif subtype == '04' or subtype == '01' or subtype == '03':
				command = "Not implemented in RFXCMD"

	# ---------------------------------------
	# 0x40 - Thermostat1
	# Credit: Jean-François Pucheu
	# ---------------------------------------
	if packettype == '40':

		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Temperature
		temperature = int(ByteToHex(message[6]), 16)

		# Temperature set
		temperature_set = int(ByteToHex(message[7]), 16)

		# Status
		status_temp = str(testBit(int(ByteToHex(message[8]),16),0) + testBit(int(ByteToHex(message[8]),16),1))
		status = rfx.rfx_subtype_40_status[status_temp]

		# Mode
		if testBit(int(ByteToHex(message[8]),16),7) == 128:
			mode = rfx.rfx_subtype_40_mode['1']
		else:
			mode = rfx.rfx_subtype_40_mode['0']
		
		#  Signal
		signal = decodeSignal(message[9])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_40[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Temperature\t\t= " + str(temperature) + " C"
			print "Temperature set\t\t= " + str(temperature_set) + " C"
			print "Mode\t\t\t= " + mode
			print "Status\t\t\t= " + status
			print "Signal level\t\t= " + str(signal)

		# CSV 
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), mode, status, str(temperature_set), str(temperature) ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, mode, status, 0, 0, 0, temperature_set, temperature, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, mode, status, 0, 0, 0, temperature_set, temperature, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x41 Thermostat2
	# ---------------------------------------
	if packettype == '41':

		decoded = True
		
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_41[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x42 Thermostat3
	# ---------------------------------------
	if packettype == '42':

		decoded = True

		# unitcode & command
		if subtype == '00':
			unitcode = byteToHex(message[4])
		elif subtype == '01':
			unitcode = byteToHex(message[4]) + byteToHex(message[5]) + byteToHex(message[6])
		else:
			unitcode = "00"

		# Command
		command = byteToHex(message[7])

		# Signal
		signal = decodeSignal(message[8])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_42[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Unitcode\t\t\t= " + unitcode
			
			if subtype == '00':
				print "" + rfx.rfx_subtype_42_cmnd00[command]
			elif subtype == '01':
				print "" + rfx.rfx_subtype_42_cmnd01[command]
			else:
				print "Unknown"

		# CSV 
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %(timestamp, packettype, subtype, seqnbr, str(signal), str(temperature_set), str(mode), str(status), str(temperature) ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, 0, 0, temperature_set, mode, status, temperature, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, 0, 0, temperature_set, mode, status, temperature, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x50 - Temperature sensors
	# ---------------------------------------
	if packettype == '50':
	
		decoded = True

		# Id
		sensor_id = id1 + id2

		# Temperature
		temperature = decodeTemperature(message[6], message[7])

		# Battery & Signal
		signal = decodeSignal(message[8])
		battery = decodeBattery(message[8])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_50[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Temperature\t\t= " + temperature + " C"
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, str(battery), str(signal), temperature ))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x51 - Humidity sensors
	# ---------------------------------------

	if packettype == '51':
		
		decoded = True

		# Signal id
		signal_id = id1 + id2

		# Humidity
		humidity = int(ByteToHex(message[6]),16)
		humidity_status = rfx.rfx_subtype_51_humstatus[ByteToHex(message[7])]

		# Battery & Signal
		signal = decodeSignal(message[8])
		battery = decodeBattery(message[8])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_51[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + signal_id
			print "Humidity\t\t= " + str(humidity)
			print "Humidity Status\t\t= " + humidity_status
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
		
		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, timeutc, packettype, subtype, seqnbr, signal_id, humidity_status,
							str(humidity), str(battery), str(signal)) )

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# XPL
		if cmdarg.xpl == True:
			xpl.send(config.xplhost, 'device=Hum.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%')
			xpl.send(config.xplhost, 'device=Hum.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xplhost, 'device=Hum.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x52 - Temperature and humidity sensors
	# ---------------------------------------
	if packettype == '52':
		
		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Temperature
		temperature = decodeTemperature(message[6], message[7])

		# Humidity
		humidity = int(ByteToHex(message[8]),16)
		humidity_status = rfx.rfx_subtype_52_humstatus[ByteToHex(message[9])]

		# Battery & Signal
		signal = decodeSignal(message[10])
		battery = decodeBattery(message[10])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_52[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Temperature\t\t= " + temperature + " C"
			print "Humidity\t\t= " + str(humidity) + "%"
			print "Humidity Status\t\t= " + humidity_status
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
		
		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, timeutc, packettype, subtype, seqnbr, sensor_id, humidity_status,
							temperature, str(humidity), str(battery), str(signal)) )
		
		# GRAPHITE
		if cmdarg.graphite == True:
			now = int( time.time() )
			linesg=[]
			linesg.append("%s.%s.temperature %s %d" % ( sensor_id, temperature,now))
			linesg.append("%s.%s.humidity %s %d" % ( sensor_id, humidity,now))
			linesg.append("%s.%s.battery %s %d" % ( sensor_id, battery,now))
			linesg.append("%s.%s.signal %s %d"% ( sensor_id, signal,now))
			send_graphite(config.graphite_server, config.graphite_port, linesg)

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# XPL
		if cmdarg.xpl == True:
			xpllib.send(config.xplhost, 'device=HumTemp.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C')
			xpllib.send(config.xplhost, 'device=HumTemp.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=HumTemp.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=HumTemp.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x54 - Temperature, humidity and barometric sensors
	# Credit: Jean-Baptiste Bodart
	# ---------------------------------------
	if packettype == '54':
		
		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Temperature
		temperature = decodeTemperature(message[6], message[7])
		
		# Humidity
		humidity = int(ByteToHex(message[8]),16)
		humidity_status = rfx.rfx_subtype_54_humstatus[ByteToHex(message[9])]

		# Barometric pressure
		barometric_high = ByteToHex(message[10])
		barometric_low = ByteToHex(message[11])
		barometric_high = clearBit(int(barometric_high,16),7)
		barometric_high = barometric_high << 8
		barometric = ( barometric_high + int(barometric_low,16) )
		
		# Forecast
		forecast = rfx.rfx_subtype_54_forecast[ByteToHex(message[12])]
		
		# Battery & Signal
		signal = decodeSignal(message[13])
		battery = decodeBattery(message[13])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_54[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Temperature\t\t= " + temperature + " C"
			print "Humidity\t\t= " + str(humidity)
			print "Humidity Status\t\t= " + humidity_status			
			print "Barometric pressure\t= " + str(barometric)
			print "Forecast Status\t\t= " + forecast
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
		
		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id,
							forecast, humidity_status, str(humidity), str(baormetric), str(temperature)))
		
		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, forecast, humidity_status, humidity, barometric, 0, 0, temperature, 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, forecast, humidity_status, humidity, barometric, 0, 0, temperature, 0, 0, 0, 0, 0)

		# XPL
		if cmdarg.xpl == True:
			xpllib.send(config.xplhost, 'device=HumTempBaro.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C')
			xpllib.send(config.xplhost, 'device=HumTempBaro.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=HumTempBaro.'+sensor_id+'\ntype=humidity\ncurrent='+str(barometric)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=HumTempBaro.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=HumTempBaro.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x55 - Rain sensors
	# ---------------------------------------
	
	if packettype == '55':
		
		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Rain rate
		rainrate_high = ByteToHex(message[6])
		rainrate_low = ByteToHex(message[7])

		# Rain total
		raintotal1 = ByteToHex(message[8])
		raintotal2 = ByteToHex(message[9])
		raintotal3 = ByteToHex(message[10])
		
		# Battery & Signal	
		signal = decodeSignal(message[11])
		battery = decodeBattery(message[11])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_55[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			
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
		
		# CSV		
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							( timestamp, packettype, subtype, seqnbr, id1, id2,
							str(int(rainrate_high,16)), str(int(raintotal1,16)), 
							str(battery), str(signal) ) )

		"""			
		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)
		"""

	# ---------------------------------------
	# 0x56 - Wind sensors
	# ---------------------------------------
	if packettype == '56':
		
		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Direction
		direction = ( ( int(ByteToHex(message[6]),16) * 256 ) + int(ByteToHex(message[7]),16) )
		
		# AV Speed
		if subtype <> "05":
			av_speed = ( ( int(ByteToHex(message[8]),16) * 256 ) + int(ByteToHex(message[9]),16) ) * 0.1
		else:
			av_speed = 0;
			
		# Gust
		gust = ( ( int(ByteToHex(message[10]),16) * 256 ) + int(ByteToHex(message[11]),16) ) * 0.1

		# Temperature	
		if subtype == "04":
			temperature = decodeTemperature(message[12], message[13])
		else:
			temperature = 0

		# Windchill
		if subtype == "04":
			windchill = decodeTemperature(message[14], message[15])
		else:
			windchill = 0
		
		# Battery & Signal
		signal = decodeSignal(message[16])
		battery = decodeBattery(message[16])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_56[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Wind direction\t\t= " + str(direction) + " degrees"
			
			if subtype <> "05":
				print "Average wind\t\t= " + str(av_speed) + " mtr/sec"
			
			if subtype == "04":
				print "Temperature\t\t= " + str(temperature) + " C"
				print "Wind chill\t\t= " + str(windchill) + " C" 
			
			print "Windgust\t\t= " + str(gust) + " mtr/sec"
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id,
							str(temperature), str(av_speed), str(gust), str(direction), str(windchill) ) )
	
		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)

	# ---------------------------------------
	# 0x59 Current Sensor
	# ---------------------------------------

	if packettype == '59':

		decoded = True

		# Sensor ID
		sensor_id = id1 + id2

		# Counter
		count = int(ByteToHex(message[6]),16)

		channel1 = (int(ByteToHex(message[7]),16) * 0x100 + int(ByteToHex(message[8]),16)) * 0.1
		channel2 = int(ByteToHex(message[9]),16) * 0x100 + int(ByteToHex(message[10]),16)
		channel3 = int(ByteToHex(message[11]),16) * 0x100 + int(ByteToHex(message[12]),16)

		# Battery & Signal
		signal = decodeSignal(message[13])
		battery = decodeBattery(message[13])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_5A[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Counter\t\t\t= " + str(count)
			print "Channel 1\t\t= " + str(channel1) + "A"
			print "Channel 2\t\t= " + str(channel2) + "A"
			print "Channel 3\t\t= " + str(channel3) + "A"
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
	
		# XPL
		if cmdarg.xpl == True:
			xpllib.send(config.xplhost, 'device=Current.'+sensor_id+'\ntype=channel1\ncurrent='+str(channel1)+'\nunits=A')
			xpllib.send(config.xplhost, 'device=Current.'+sensor_id+'\ntype=channel2\ncurrent='+str(channel2)+'\nunits=A')
			xpllib.send(config.xplhost, 'device=Current.'+sensor_id+'\ntype=channel3\ncurrent='+str(channel3)+'\nunits=A')
			xpllib.send(config.xplhost, 'device=Current.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=Current.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x5A Energy sensor
	# Credit: Jean-Michel ROY
	# ---------------------------------------
	if packettype == '5A':

		decoded = True

		# Sensor id
		sensor_id = id1 + id2

		# Battery & Signal
		signal = decodeSignal(message[17])
		battery = decodeBattery(message[17])

		# Power
		instant = int(ByteToHex(message[7]), 16) * 0x1000000 + int(ByteToHex(message[8]), 16) * 0x10000 + int(ByteToHex(message[9]), 16) * 0x100  + int(ByteToHex(message[10]), 16)
		usage = int ((int(ByteToHex(message[11]), 16) * 0x10000000000 + int(ByteToHex(message[12]), 16) * 0x100000000 +int(ByteToHex(message[13]), 16) * 0x1000000 + int(ByteToHex(message[14]), 16) * 0x10000 + int(ByteToHex(message[15]), 16) * 0x100 + int(ByteToHex(message[16]), 16) ) / 223.666)

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_5A[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Instant usage\t\t= " + str(instant) + " Watt"
			print "Total usage\t\t= " + str(usage) + " Wh"
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id,
							str(instant), str(usage), str(battery), str(signal)) )

		# XPL
		if cmdarg.xpl == True:
			xpllib.send(config.xplhost, 'device=Energy.'+sensor_id+'\ntype=instant_usage\ncurrent='+str(channel1)+'\nunits=W')
			xpllib.send(config.xplhost, 'device=Energy.'+sensor_id+'\ntype=total_usage\ncurrent='+str(channel2)+'\nunits=Wh')
			xpllib.send(config.xplhost, 'device=Energy.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpllib.send(config.xplhost, 'device=Energy.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x5B Current + Energy sensor
	# ---------------------------------------
	
	# TODO
	
	# ---------------------------------------
	# 0x70 RFXsensor
	# ---------------------------------------
	if packettype == '70':

		decoded = True

		# Temperature
		if subtype == '00':
			temperature = float(decodeTemperature(message[5], message[6]))
			temperature = temperature * 0.1
		else:
			temperature = 0

		# Voltage
		if subtype == '01' or subtype == '02':
			voltage_hi = int(ByteToHex(message[5]), 16) * 256
			voltage_lo = int(ByteToHex(message[6]), 16)
			voltage = voltage_hi + voltage_lo
		else:
			voltage = 0

		# Signal
		signal = decodeSignal(message[7])

		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_70[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + id1

			if subtype == '00':
				print "Temperature\t\t= " + str(temperature) + " C"

			if subtype == '01' or subtype == '02':
				print "Voltage\t\t\t= " + str(voltage) + " mV"

			if subtype == '03':
				print "Message\t\t\t= " + rfx.rfx_subtype_70_msg03[message[6]]

			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv == True:
			if subtype == '00':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, str(temperature)))
			if subtype == '01' or subtype == '02':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, str(voltage)))

		# MYSQL
		if cmdarg.mysql:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, id1, ByteToHex(message[5]), ByteToHex(message[6]), 0, 0, 0, voltage, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if cmdarg.sqlite:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, id1, ByteToHex(message[5]), ByteToHex(message[6]), 0, 0, 0, voltage, float(temperature), 0, 0, 0, 0, 0)

	# ---------------------------------------
	# Not decoded message
	# ---------------------------------------	
	
	# The packet is not decoded, then print it on the screen
	if decoded == False:
		print timestamp + " " + ByteToHex(message)
		print "RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/ for more information."

	# decodePackage END
	return

# ----------------------------------------------------------------------------
# DECODE THE MESSAGE AND SEND TO RFX
# ----------------------------------------------------------------------------

def send_rfx( message ):
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	
	if cmdarg.printout_complete == True:
		print "------------------------------------------------"
		print "Send\t\t\t= " + ByteToHex( message )
		print "Date/Time\t\t= " + timestamp
		print "Packet Length\t\t= " + ByteToHex( message[0] )
		
		try:
			decodePacket( message )
		except KeyError:
			print "Error: unrecognizable packet"
	
	serial_param.port.write( message )
	time.sleep(1)

# ----------------------------------------------------------------------------
# READ DATA FROM RFX AND DECODE THE MESSAGE
# ----------------------------------------------------------------------------

def read_rfx():

	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	logdebug('Timestamp: ' + timestamp)
	message = None

	try:
		byte = serial_param.port.read()
		logdebug('Byte: ' + str(ByteToHex(byte)))
		
		if byte:
			message = byte + readbytes( ord(byte) )
			logdebug('Message: ' + str(ByteToHex(message)))
			
			if ByteToHex(message[0]) <> "00":
			
				# Verify length
				logdebug('Verify length')
				if (len(message) - 1) == ord(message[0]):
				
					logdebug('Length OK')
					if cmdarg.printout_complete == True:
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
				
					if cmdarg.printout_complete == True:
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
 		logerror('Config file does not exists')
 		
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
# PRINT RFXCMD VERSION
# ----------------------------------------------------------------------------

def print_version():
	logdebug("def print_version")
 	print "RFXCMD Version: " + __version__
 	print __date__.replace('$', '')
 	logdebug("Exit 0")
 	sys.exit(0)

# ----------------------------------------------------------------------------
# CHECK PYTHON VERSION
# ----------------------------------------------------------------------------

def check_pythonversion():
	logdebug("Python version: %s.%s.%s" % sys.version_info[:3])
	if sys.hexversion < 0x02060000:
		logerror("Error: Your Python need to be 2.6 or newer, please upgrade.")
		print "Error: Your Python need to be 2.6 or newer, please upgrade."
		logdebug("Exit 1")
		sys.exit(1)

# ----------------------------------------------------------------------------
# SIMULATE INCOMING PACKET
# ----------------------------------------------------------------------------

def option_simulate(indata):

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

	#indata = options.simulate
	
	# remove all spaces
	for x in string.whitespace:
		indata = indata.replace(x,"")
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	
	if cmdarg.printout_complete:
		print "------------------------------------------------"
		print "Received\t\t= " + indata
		print "Date/Time\t\t= " + timestamp
	
	# Verify that the incoming value is hex
	try:
		hexval = int(indata, 16)
	except:
		logerror("Error: the input data is invalid hex value")
		print "Error: the input data is invalid hex value"
		exit()
	
	# cut into hex chunks
	try:
		message = indata.decode("hex")
	except:
		logerror("Error: the input data is not valid")
		print "Error: the input data is not valid"
		exit()
	
	# decode it
	try:
		decodePacket( message )
	except KeyError:
		logerror("Error: unrecognizable packet")
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
# LISTEN TO RFXtrx DEVICE
# ----------------------------------------------------------------------------

def option_listen():

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
	serial_param.port.flushOutput()
	logdebug('Serialport flush input')
	serial_param.port.flushInput()

	# Send RESET
	logdebug('Send rfxcmd_reset (' + rfxcmd.reset + ')')
	serial_param.port.write( rfxcmd.reset.decode('hex') )
	logdebug('Sleep 1 sec')
	time.sleep(1)

	# Flush buffer
	logdebug('Serialport flush output')
	serial_param.port.flushOutput()
	logdebug('Serialport flush input')
	serial_param.port.flushInput()

	if config.undecoded:
		logdebug('Send rfxcmd_undecoded (' + rfxcmd.undecoded + ')')
		send_rfx( rfxcmd.undecoded.decode('hex') )
		logdebug('Sleep 1 sec')
		time.sleep(1)
		logdebug('Read_rfx')
		read_rfx()
		
	# Send STATUS
	logdebug('Send rfxcmd_status (' + rfxcmd.status + ')')
	serial_param.port.write( rfxcmd.status.decode('hex') )
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
# GET STATUS FROM RFXtrx DEVICE
# ----------------------------------------------------------------------------

def option_getstatus():

	# Flush buffer
	serial_param.port.flushOutput()
	serial_param.port.flushInput()

	# Send RESET
	serial_param.port.write(rfxcmd.reset.decode('hex'))
	time.sleep(1)

	# Flush buffer
	serial_param.port.flushOutput()
	serial_param.port.flushInput()

	if config.undecoded:
		send_rfx(rfxcmd.undecoded.decode('hex'))
		time.sleep(1)
		read_rfx()
		
	# Send STATUS
	send_rfx(rfxcmd.status.decode('hex'))
	time.sleep(1)
	read_rfx()

# ----------------------------------------------------------------------------
# SEND COMMAND
# ----------------------------------------------------------------------------

def option_send():

	logdebug('Action: send')

	# Remove any whitespaces	
	cmdarg.rawcmd = cmdarg.rawcmd.replace(' ', '')
	logdebug('rawcmd: ' + cmdarg.rawcmd)

	# Test the string if it is hex format
	try:
		int(cmdarg.rawcmd,16)
	except ValueError:
		print "Error: invalid rawcmd, not hex format"
		sys.exit(1)		
	
	# Check that first byte is not 00
	if ByteToHex(cmdarg.rawcmd.decode('hex')[0]) == "00":
		print "Error: invalid rawcmd, first byte is zero"
		sys.exit(1)
	
	# Check if string is the length that it reports to be
	cmd_len = int( ByteToHex(cmdarg.rawcmd.decode('hex')[0]),16 )
	if not len(cmdarg.rawcmd.decode('hex')) == (cmd_len + 1):
		print "Error: invalid rawcmd, invalid length"
		sys.exit(1)

	# Flush buffer
	serial_param.port.flushOutput()
	serial_param.port.flushInput()

	# Send RESET
	serial_param.port.write( rfxcmd.reset.decode('hex') )
	time.sleep(1)

	# Flush buffer
	serial_param.port.flushOutput()
	serial_param.port.flushInput()

	if config.undecoded:
		send_rfx( rfxcmd.undecoded.decode('hex') )
		time.sleep(1)
		read_rfx()
		
	if cmdarg.rawcmd:
		timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
		if cmdarg.printout_complete == True:
			print "------------------------------------------------"
			print "Send\t\t\t= " + ByteToHex( cmdarg.rawcmd.decode('hex') )
			print "Date/Time\t\t= " + timestamp
			print "Packet Length\t\t= " + ByteToHex( cmdarg.rawcmd.decode('hex')[0] )
			try:
				decodePacket( cmdarg.rawcmd.decode('hex') )
			except KeyError:
				print "Error: unrecognizable packet"

		serial_param.port.write( cmdarg.rawcmd.decode('hex') )
		time.sleep(1)
		read_rfx()

# ----------------------------------------------------------------------------
# SEND BACKGROUND COMMAND
# ----------------------------------------------------------------------------

def option_bsend():
	
	logdebug('Action: bsend')
	
	# Remove any whitespaces
	cmdarg.rawcmd = cmdarg.rawcmd.replace(' ', '')
	logdebug('rawcmd: ' + cmdarg.rawcmd)
	
	# Test the string if it is hex format
	try:
		int(cmdarg.rawcmd,16)
	except ValueError:
		print "Error: invalid rawcmd, not hex format"
		sys.exit(1)		
	
	# Check that first byte is not 00
	if ByteToHex(cmdarg.rawcmd.decode('hex')[0]) == "00":
		print "Error: invalid rawcmd, first byte is zero"
		sys.exit(1)
	
	# Check if string is the length that it reports to be
	cmd_len = int( ByteToHex( cmdarg.rawcmd.decode('hex')[0]),16 )
	if not len(cmdarg.rawcmd.decode('hex')) == (cmd_len + 1):
		print "Error: invalid rawcmd, invalid length"
		sys.exit(1)

	if cmdarg.rawcmd:
		serial_param.port.write(cmdarg.rawcmd.decode('hex'))

# ----------------------------------------------------------------------------

def read_configfile():
	"""
	Read the configuration file
	"""
	if os.path.exists( cmdarg.configfile ):

		# RFX configuration
		if ( read_config( cmdarg.configfile, "undecoded") == "yes"):
			config.undecoded = True
		else:
			config.undecoded = False

		# MySQL configuration
		config.mysql_server = read_config( cmdarg.configfile, "mysql_server")
		config.mysql_database = read_config( cmdarg.configfile, "mysql_database")
		config.mysql_username = read_config( cmdarg.configfile, "mysql_username")
		config.mysql_password = read_config( cmdarg.configfile, "mysql_password")
	
		if ( read_config( cmdarg.configfile, "trigger") == "yes"):
			config.trigger = True
		else:
			config.trigger = False

		config.triggerfile = read_config( cmdarg.configfile, "triggerfile")	

		# SQLite configuration
		config.sqlite_database = read_config( cmdarg.configfile, "sqlite_database")
		config.sqlite_table = read_config( cmdarg.configfile, "sqlite_table")
	
		# Configuration for Graphite server
		config.graphite_server = read_config( cmdarg.configfile, "graphite_server")
		config.graphite_port = read_config( cmdarg.configfile, "graphite_port")

		# XPL host
		config.xplhost = read_config( cmdarg.configfile, "xplhost")

	else:

		# config file not found, set default values
		print "Error: Configuration file not found (" + cmdarg.configfile + ")"
		logerror('Error: Configuration file not found (' + cmdarg.configfile + ')')

# ----------------------------------------------------------------------------

def open_serialport():
	"""
	Open serial port for communication to the RFXtrx device.
	"""

	# Check that serial module is loaded
	try:
		logdebug("Serial extension version: " + serial.VERSION)
	except:
		print "Error: You need to install Serial extension for Python"
		logdebug("Error: Serial extension for Python could not be loaded")
		logdebug("Exit 1")
		sys.exit(1)

	# Check for serial device
	if config.device:
		logdebug("Device: " + config.device)
	else:
		logerror('Device name missing')
		print "Serial device is missing"
		logdebug("Exit 1")
		sys.exit(1)

	# Open serial port
	logdebug("Open Serialport")
	try:  
		serial_param.port = serial.Serial(config.device, serial_param.rate, timeout=serial_param.timeout)
	except serial.SerialException, e:
		logerror("Error: Failed to connect on device " + config.device)
		print "Error: Failed to connect on device " + config.device
		print "Error: " + str(e)
		logdebug("Exit 1")
		sys.exit(1)

	if not serial_param.port.isOpen():
		serial_param.port.open()

# ----------------------------------------------------------------------------

def close_serialport():
	"""
	Close serial port.
	"""

	logdebug('Close serial port')
	try:
		serial_param.port.close()
		logdebug('Serial port closed')
	except:
		logdebug("Failed to close the serial port '" + device + "'")
		print "Error: Failed to close the port " + device
		logdebug("Exit 1")
		sys.exit(1)

# ----------------------------------------------------------------------------

def loghandler():
	"""
	Loghandler activates the logging.
	Used mostly for debuging

	Available loglevels are : DEBUG and ERROR
	"""
	global logger

	dom = None

	if os.path.exists( os.path.join(config.program_path, "config.xml") ):

		# Read config file
		f = open(os.path.join(config.program_path, "config.xml"),'r')
		data = f.read()
		f.close()

		try:
			dom = parseString(data)
		except:
			print "Error: problem in the config.xml file, cannot process it"

		if dom:
			try:
				xmlTag = dom.getElementsByTagName( 'loglevel' )[0].toxml()
				config.loglevel = xmlTag.replace('<loglevel>','').replace('</loglevel>','')
			except:
				pass
	
			config.loglevel = config.loglevel.upper()
	
			if config.loglevel == 'DEBUG' or config.loglevel == 'ERROR':
				logger = logging.getLogger('rfxcmd')
				hdlr = logging.FileHandler( os.path.join(config.program_path, "rfxcmd.log") )
				formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
				hdlr.setFormatter(formatter)
				logger.addHandler(hdlr) 
				logger.setLevel(config.loglevel)

# ----------------------------------------------------------------------------

def main():

	#pdb.set_trace()

	# Get directory of the rfxcmd script
	config.program_path = os.path.dirname(os.path.realpath(__file__))

	# Start loghandler
	loghandler()

	logdebug("RFXCMD Version: " + __version__)
	logdebug(__date__.replace('$', ''))

	logdebug("Parse command line")

	parser = OptionParser()
	parser.add_option("-d", "--device", action="store", type="string", dest="device", help="The serial device of the RFXCOM, example /dev/ttyUSB0")
	parser.add_option("-a", "--action", action="store", type="string", dest="action", help="Specify which action: LISTEN (default), STATUS, SEND, BSEND")
	parser.add_option("-o", "--config", action="store", type="string", dest="config", help="Specify the configuration file")
	parser.add_option("-x", "--simulate", action="store", type="string", dest="simulate", help="Simulate one incoming data message")
	parser.add_option("-r", "--rawcmd", action="store", type="string", dest="rawcmd", help="Send raw message (need action SEND)")
	parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, help="Output data in CSV format")
	parser.add_option("-l", "--xpl", action="store_true", dest="xpl", default=False, help="Send data to XPL broadcast network")
	parser.add_option("-m", "--mysql", action="store_true", dest="mysql", default=False, help="Insert data to MySQL database")
	parser.add_option("-s", "--sqlite", action="store_true", dest="sqlite", default=False, help="Insert data to SQLite database")
	parser.add_option("-g", "--graphite", action="store_true", dest="graphite", default=False, help="Send data to graphite server")
	parser.add_option("-z", "--daemonize", action="store_true", dest="daemon", default=False, help="Daemonize RFXCMD")
	parser.add_option("-p", "--pidfile", action="store", type="string", dest="pidfile", help="PID File location and name")
	parser.add_option("-v", "--version", action="store_true", dest="version", help="Print rfxcmd version information")

	(options, args) = parser.parse_args()

	if options.version:
		print_version()

	if options.csv:
		logdebug("Option: CSV chosen")
		cmdarg.printout_complete = False
		cmdarg.printout_csv = True

	if options.mysql:
		logdebug("Option: MySQL chosen")
		cmdarg.printout_complete = False
		cmdarg.printout_csv = False

	if options.sqlite:
		logdebug("Option: SqLite chosen")
		cmdarg.printout_complete = False
		cmdarg.printout_csv = False

	if cmdarg.printout_complete == True:
		if not options.daemon:
			print "RFXCMD Version " + __version__

	# Serial device
	if options.device:
		config.device = options.device
	else:
		config.device = None

	# Config file
	if options.config:
		cmdarg.configfile = options.config
	else:
		cmdarg.configfile = os.path.join(config.program_path, "config.xml")

	logdebug("Configfile: " + cmdarg.configfile)

	# Graphite
	if options.graphite:
		cmdarg.graphite = True
		logdebug("Option: Graphite chosen")

	# Deamon
	if options.daemon:
		logdebug("Option: Daemon chosen")
		logdebug("Check PID file")
		
		if options.pidfile:
			cmdarg.pidfile = options.pidfile
			cmdarg.createpid = True
			logdebug("PID file '" + cmdarg.pidfile + "'")
		
			if os.path.exists(cmdarg.pidfile):
				print("PID file '" + cmdarg.pidfile + "' already exists. Exiting.")
				logdebug("PID file '" + cmdarg.pidfile + "' already exists.")
				logdebug("Exit 1")
				sys.exit(1)
			else:
				logdebug("PID file does not exists")

		else:
			print("You need to set the --pidfile parameter at the startup")
			logdebug("Command argument --pidfile missing")
			logdebug("Exit 1")
			sys.exit(1)

		logdebug("Check platform")
		if sys.platform == 'win32':
			print "Daemonize not supported under Windows. Exiting."
			logdebug("Daemonize not supported under Windows.")
			logdebug("Exit 1")
			sys.exit(1)
		else:
			logdebug("Platform: " + sys.platform)
			
			try:
				logdebug("Write PID file")
				file(cmdarg.pidfile, 'w').write("pid\n")
			except IOError, e:
				logdebug("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))
				raise SystemExit("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))

			logdebug("Deactivate screen printouts")
			cmdarg.printout_complete = False

			logdebug("Start daemon")
			daemonize()

	# XPL
	if options.xpl:
		logdebug("Option: XPL chosen")
		cmdarg.printout_complete = True
		cmdarg.xpl = options.xpl

	# MySQL
	if options.mysql == True:
		cmdarg.mysql = True

	# SqLite
	if options.sqlite == True:
		cmdarg.sqlite = True
		logdebug("Check sqlite3")
		try:
			logdebug("SQLite3 version: " + sqlite3.sqlite_version)
		except ImportError:
			print "Error: You need to install SQLite extension for Python"
			logdebug("Error: Could not find MySQL extension for Python")
			logdebug("Exit 1")
			sys.exit(1)

	# Action
	if options.action:
		cmdarg.action = options.action.lower()
		if not (cmdarg.action == "listen" or cmdarg.action == "send" or
			cmdarg.action == "bsend" or cmdarg.action == "status"):
			logerror("Error: Invalid action")
			parser.error('Invalid action')
	else:
		cmdarg.action = "listen"

	logdebug("Action chosen: " + cmdarg.action)

	# Rawcmd
	if cmdarg.action == "send" or cmdarg.action == "bsend":
		cmdarg.rawcmd = options.rawcmd
		if not cmdarg.rawcmd:
			print "Error: You need to specify message to send with -r <rawcmd>. Exiting."
			logerror("Error: You need to specify message to send with -r <rawcmd>")
			logdebug("Exit 1")
			sys.exit(1)
	
		logdebug("Rawcmd: " + cmdarg.rawcmd)

	read_configfile()

	if options.simulate:
		option_simulate( options.simulate )

	open_serialport()

	if cmdarg.action == "listen":
		option_listen()

	if cmdarg.action == "status":
		option_getstatus()

	if cmdarg.action == "send":
		option_send()

	if cmdarg.action == "bsend":
		option_bsend()

	close_serialport()

	logdebug("Exit 0")
	sys.exit(0)

# ------------------------------------------------------------------------------

if __name__ == '__main__':

	# Init shutdown handler
	signal.signal(signal.SIGINT, handler)
	signal.signal(signal.SIGTERM, handler)

	# Init objects
	config = config_data()
	cmdarg = cmdarg_data()
	rfx = rfx_data()
	rfxcmd = rfxcmd_data()
	serial_param = serial_data()

	# Check python version
	check_pythonversion()
	
	main()

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
