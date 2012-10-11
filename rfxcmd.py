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
#	Revision History
#	
#	v0.1	06-JUL-2012 
#			* Created, first working version, Reference : RFXtrx SDK 4.24 
#			
#	v0.1b	10-JUL-2012 
#			* Fixed temperature decoding for (device 0x52) 
#			* Flush I/O buffer before first command
#			* Print the polarity sign (device 0x52)
#			
#	v0.1c	11-JUL-2012
#			* Check that Python is 2.6 or newer
#			* If first receiving byte is 00 then don't start decoding
#			* Better error handling
#			
#	v0.1d	12-JUL-2012
#			* Added simulate function (-x) to decode data manually
#
#	v0.1e	28-JUL-2012
#			* Fixed MySQL issue, if password is wrong
#			
#	v0.1f	06-SEP-2012
#			* Handle exception if serial lib does not exist
#			* Compatible with RFX SDK version 4.30
#			* Added all missing receive subgroups
#			* Corrected protocol printout in status
#			* New switch (-a) to choose action LISTEN or STATUS
#			
#	v0.1g	09-SEP-2012
#			* Added process for Humidity Sensors (0x51)
#			* Added process for Wind Sensors (0x56)
#			* Compatible with RFX SDK version 4.31
#			* Added CM180/ELEC3 (v4.31)
#
#	v0.1h	06-SEP-2012
#			* Added possibility for enable all RF
#			* Added possibility for enable undecoded messages
#			* Fix for "Issue 1:	Error when trying to store to MySql"
#			* Added 0x12 Lighting3
#			* Added 0x13 Lighting4
#			* Updated to support FW version 433_50 (14-9-2012)
#			* Added configuration file (config.xml)
#			* Added to send raw messages
#			* Handle exception in serialport.read()
#			* Trigger on specific messages
#			* Added support for 0x54 (Credit: Jean-Baptiste Bodart)
#			* Added support for 0x5A (Credit: Jean-Michel ROY)
#			* Corrected singnal/battery (Thanks: Jean-Baptiste Bodart)
#
#	v0.1j	08-OCT-2012
#			* Added regex in the trigger function (Thanks: Robert F)
#			* If config file not found, print error and set default values
#			* Verify message length with reported length before decode
#			* Fix for "Issue #2: Problem with temperatures below 0 degrees Celsius"
#			* Corrected MySQL statement in 0x5A (Thanks: Dimitri)
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

from xml.dom.minidom import parseString
import xml.dom.minidom as minidom
from optparse import OptionParser

# Import Serial
try:
	import serial
except ImportError:
	print "Error: You need to install Serial extension for Python"
	sys.exit(1)

sw_name = "RFXCMD"
sw_version = "0.1j"

# ----------------------------------------------------------------------------
# DEFAULT CONFIGURATION PARAMETERS
# ----------------------------------------------------------------------------

# If the config.xml does not exist, or can not be loaded, this is the
# default configuration which will be used

_config_enableallrf = False
_config_undecoded = False
_config_mysql_server = ""
_config_mysql_database = ""
_config_mysql_username = ""
_config_mysql_password = ""
	
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
		
	global _config_printout_csv, _config_printout_complete
	global _config_mysql_server, _config_mysql_username, _config_mysql_password, _config_mysql_database
	
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
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_11[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Housecode\t\t= " + ByteToHex(message[4])
			print "Unitcode\t\t= " + ByteToHex(message[5])
			print "Command\t\t\t= " + ByteToHex(message[6])
			# TODO
			
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
			
			rssi = str(int(ByteToHex(message[11]),16) & 0xf)
			print "RSSI\t\t\t= " + ByteToHex(message[10])
			
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
	# ---------------------------------------
	if packettype == '15':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_15[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

	# ---------------------------------------
	# 0x18 Curtain1
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
	# ---------------------------------------
	if packettype == '20':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_20[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

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
	# 0x40 Thermostat1
	# ---------------------------------------
	if packettype == '40':

		decoded = True
		
		if printout_complete == True:
			print "Subtype\t\t\t= " + rfx_subtype_40[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

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

		batt_rssi = ByteToHex(message[8])		
		signal = int(batt_rssi,16) >> 4
		battery = int(batt_rssi,16) & 0xf
		
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

				db = MySQLdb.connect(_config_mysql_server, _config_mysql_username, _config_mysql_password, _config_mysql_database)
				cursor = db.cursor()

				cursor.execute("INSERT INTO weather \
				(datetime, packettype, subtype, seqnbr, id1, id2, temperature, battery, signal_level) VALUES \
				('%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
				(timestamp, packettype, subtype, seqnbr, id1, id2, temperature_str, battery, signal))
				
				db.commit()

			except MySQLdb.Error, e:

				print "Error %d: %s" % (e.args[0], e.args[1])
				sys.exit(1)

			finally:

				if db:
					db.close()

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
			
			print "Battery (0-9)\t\t= " + str(battery)
			print "Signal level (0-15)\t= " + str(signal)
		
		if printout_csv == True:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, packettype, subtype, seqnbr, id1, id2,
							str(int(humidity,16)), humidity_status, 
							str(battery), str(signal)) )
		
		if options.mysql:

			try:
				db = MySQLdb.connect(_config_mysql_server, _config_mysql_username, _config_mysql_password, _config_mysql_database)
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
		
		if options.mysql:

			try:
				db = MySQLdb.connect(_config_mysql_server, _config_mysql_username, _config_mysql_password, _config_mysql_database)
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
				db = MySQLdb.connect(mysql_server, mysql_username, mysql_password, mysql_database)
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

		# Chill factor (15,16,17)
		if subtype == "04":
			chill_high = ByteToHex(message[15])
			chill_low = ByteToHex(message[16])
			chill_pol = testBit(int(chill_high,16),15)
		
			if chill_pol == 1:
				chill_pol_sign = "-"
			else:
				chill_pol_sign = ""

			chill_high = clearBit(int(temp_high,16),7)
			chill_high = chill_high << 8
			windchill = ( int(chill_high,16) + int(chill_low,16) ) * 0.1
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
							str(battery), str(signal)) )
		
		if options.mysql:

			try:
				db = MySQLdb.connect(_config_mysql_server, _config_mysql_username, _config_mysql_password, _config_mysql_database)
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

		print "Subtype\t\t\t= " + rfx_subtype_5A[subtype]

		# Battery & Signal
		batt_rssi = ByteToHex(message[17])
		signal = int(batt_rssi,16) >> 4
		battery = int(batt_rssi,16) & 0xf

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
				db = MySQLdb.connect(_config_mysql_server, _config_mysql_username, _config_mysql_password, _config_mysql_database)
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
	# 0x5A END
	# ---------------------------------------

	# ---------------------------------------
	# Not decoded message
	# ---------------------------------------	
	
	# The packet is not decoded, then print it on the screen
	if decoded == False:
		print timestamp + " " + ByteToHex(message)
		print "RFXCMD cannot decode message, see readme.txt for more information."

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
		decodePacket( message )
	
	serialport.write( message )
	time.sleep(1)

# ----------------------------------------------------------------------------
# READ DATA FROM RFX AND DECODE THE MESSAGE
# ----------------------------------------------------------------------------

def read_rfx():

	global printout_complete, printout_csv
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

	try:
		byte = serialport.read()
		
		if byte:
			message = byte + readbytes( ord(byte) )
			
			if ByteToHex(message[0]) <> "00":
			
				# Verify length
				if (len(message) - 1) == ord(message[0]):
				
					if printout_complete == True:
						print "------------------------------------------------"
						print "Received\t\t= " + ByteToHex( message )
						print "Date/Time\t\t= " + timestamp
						print "Packet Length\t\t= " + ByteToHex( message[0] )
				
					decodePacket( message )
	
					rawcmd = ByteToHex ( message )
					rawcmd = rawcmd.replace(' ', '')

					return rawcmd
				
				else:
				
					if printout_complete == True:
						print "------------------------------------------------"
						print "Received\t\t= " + ByteToHex( message )
						print "Incoming packet not valid, waiting for next..."
				
	except OSError, e:
		print "------------------------------------------------"
		print "Received\t\t= " + ByteToHex( message )
		traceback.print_exc()

# ----------------------------------------------------------------------------
# READ ITEM FROM THE CONFIGURATION FILE
# ----------------------------------------------------------------------------

def read_config( configFile, configItem):
 
	#open the xml file for reading:
	file = open( configFile,'r')
	data = file.read()
	file.close()
	dom = parseString(data)
	
	# Get config item
	xmlTag = dom.getElementsByTagName( configItem )[0].toxml()
	xmlData=xmlTag.replace('<' + configItem + '>','').replace('</' + configItem + '>','')
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
		# print trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
		message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
		# print trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
		action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
 		triggerlist = [ message, action ]
 		# print triggerlist
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
						
rfx_subtype_01_msg4 = {"128":"BlindsT1 (433.92)",
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

rfx_subtype_10 = {"00":"lighting1"}

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

rfx_subtype_18 = {"00":"Harrison Curtain"}

rfx_subtype_19 = {"00":"BlindsT0 / Rollertrol, Hasta new",
					"01":"BlindsT1 / Hasta old"}

rfx_subtype_20 = {"00":"X10 security door/window sensor",
					"01":"X10 security motion sensor",
					"02":"X10 security remote (no alive packets)",
					"03":"KD101 (no alive packets)",
					"04":"Visonic PowerCode door/window sensor - Primary contact (with alive packets)",
					"05":"Visonic PowerCode motion sensor (with alive packets)",
					"06":"Visonic CodeSecure (no alive packets)",
					"07":"Visonic PowerCode door/window sensor - auxiliary contact (no alive packets)",
					"08":"Meiantech"}

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
rfx_enableallrf="0d00000004000000000000000000"
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

parser = OptionParser()
parser.add_option("-d", "--device", action="store", type="string", dest="device", help="The serial device of the RFXCOM, example /dev/ttyUSB0")
parser.add_option("-a", "--action", action="store", type="string", dest="action", help="Specify which action: LISTEN (default), STATUS, SEND, BSEND")
parser.add_option("-o", "--config", action="store", type="string", dest="config", help="Specify the configuration file")
parser.add_option("-x", "--simulate", action="store", type="string", dest="simulate", help="Simulate one incoming data message")
parser.add_option("-r", "--rawcmd", action="store", type="string", dest="rawcmd", help="Send raw message (need action SEND)")
parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, help="Output data in CSV format")
parser.add_option("-m", "--mysql", action="store_true", dest="mysql", default=False, help="Insert data to MySQL database")

(options, args) = parser.parse_args()

if options.csv:
	printout_complete = False
	printout_csv = True

if options.mysql:
	printout_complete = False
	printout_csv = False

if printout_complete == True:
	print sw_name + " version " + sw_version

if options.config:
	configFile = options.config
else:
	configFile = "config.xml"

if options.mysql == True:

	# Import MySQLdb
	try:
		import MySQLdb
	except ImportError:
		print "Error: You need to install MySQL extension for Python"
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

# ----------------------------------------------------------------------------
# READ CONFIGURATION FILE
# ----------------------------------------------------------------------------

if os.path.exists( configFile ):

	# RFX configuration
	if ( read_config( configFile, "enableallrf") == "yes"):
		_config_enableallrf = True
	else:
		_config_enableallrf = False

	if ( read_config( configFile, "undecoded") == "yes"):
		_config_undecoded = True
	else:
		_config_undecoded = False

	# MySQL configuration
	_config_mysql_server = read_config( configFile, "mysql_server")
	_config_mysql_database = read_config( configFile, "mysql_database")
	_config_mysql_username = read_config( configFile, "mysql_username")
	_config_mysql_password = read_config( configFile, "mysql_password")
	
	if ( read_config( configFile, "trigger") == "yes"):
		_config_trigger = True
	else:
		_config_trigger = False

	_config_triggerfile = read_config( configFile, "triggerfile")	

else:

	# config file not found, set default values
	print "Error: Configuration file not found (" + configFile + ")"
	
	_config_enableallrf = False
	_config_undecoded = False
	
	_config_mysql_server = ""
	_config_mysql_database = ""
	_config_mysql_username = ""
	_config_mysql_password = ""

	_config_trigger = False

# ----------------------------------------------------------------------------
# SIMULATE
# ----------------------------------------------------------------------------

if options.simulate:

	# If trigger is activated in config, then read the triggerfile
	if _config_trigger:
		xmldoc = minidom.parse( _config_triggerfile )
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
	decodePacket( message )
	
	if _config_trigger:
		if message:
			for trigger in triggers:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					return_code = subprocess.call(action, shell=True)
	
	sys.exit(0)

# ----------------------------------------------------------------------------
# OPEN SERIAL CONNECTION
# ----------------------------------------------------------------------------

if options.device:
	device=options.device
else:
	parser.error('Device name missing')

# Open serial port
try:  
	serialport = serial.Serial(device, 38400, timeout=9)
except:  
	print "Error: Failed to connect on " + device
	exit()

already_open = serialport.isOpen()
if not already_open:
	serialport.open()

# ----------------------------------------------------------------------------
# LISTEN TO RFX, EXIT WITH CTRL+C
# ----------------------------------------------------------------------------

if rfxcmd_action == "listen":

	# If trigger is activated in config, then read the triggerfile
	if _config_trigger:
		xmldoc = minidom.parse( _config_triggerfile )
		root = xmldoc.documentElement

		triggers = root.getElementsByTagName('trigger')

		triggerlist = []
	
		for trigger in triggers:
			message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
			action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
 			triggerlist = [ message, action ]
			
	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	# Send RESET
	serialport.write( rfx_reset.decode('hex') )
	time.sleep(1)

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	if _config_undecoded:
		send_rfx( rfx_undecoded.decode('hex') )
		time.sleep(1)
		read_rfx()
		
	if _config_enableallrf:
		send_rfx( rfx_enableallrf.decode('hex') )
		time.sleep(1)
		read_rfx()

	# Send STATUS
	serialport.write( rfx_status.decode('hex') )
	time.sleep(1)

	try:
		while 1:
			rawcmd = read_rfx()

			if _config_trigger:
				if rawcmd:
					for trigger in triggers:
						message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
						action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
						if re.match(message, rawcmd):
							return_code = subprocess.call(action, shell=True)

	except KeyboardInterrupt:
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

	if _config_undecoded:
		send_rfx( rfx_undecoded.decode('hex') )
		time.sleep(1)
		read_rfx()
		
	if _config_enableallrf:
		send_rfx( rfx_enableallrf.decode('hex') )
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

	if _config_undecoded:
		send_rfx( rfx_undecoded.decode('hex') )
		time.sleep(1)
		read_rfx()
		
	if _config_enableallrf:
		send_rfx( rfx_enableallrf.decode('hex') )
		time.sleep(1)
		read_rfx()

	if rfxcmd_rawcmd:
		timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
		if printout_complete == True:
			print "------------------------------------------------"
			print "Send\t\t\t= " + ByteToHex( rfxcmd_rawcmd.decode('hex') )
			print "Date/Time\t\t= " + timestamp
			print "Packet Length\t\t= " + ByteToHex(rfxcmd_rawcmd.decode('hex')[0])
			decodePacket( rfxcmd_rawcmd.decode('hex') )
			
		serialport.write( rfxcmd_rawcmd.decode('hex') )
		time.sleep(1)
		read_rfx()

# ----------------------------------------------------------------------------
# BSEND
# ----------------------------------------------------------------------------

if rfxcmd_action == "bsend":
	
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

	if rfxcmd_rawcmd:
		serialport.write( rfxcmd_rawcmd.decode('hex') )
	
# ----------------------------------------------------------------------------
# CLOSE SERIAL CONNECTION
# ----------------------------------------------------------------------------

try:
	serialport.close()
except:
	print "Error: Failed to close the port " + device

exit()