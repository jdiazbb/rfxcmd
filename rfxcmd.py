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
#			* Added simulate function (-s) to decode data manually
#
#	v0.1e	28-JUL-2012
#			* Fixed MySQL issue, if password is wrong
#			
#	v0.1f	06-SEP-2012
#			* Handle exception if serial lib does not exist
#			* Compatible with RFXtrx SDK version 4.30
#			* Added all missing receive subgroups
#			* Corrected protocol printout in status
#			* New switch (-a) to choose action LISTEN or STATUS
#			
#
#	NOTES
#	
#	RFXCOM is a Trademark of RFSmartLink.
#	
# ----------------------------------------------------------------------------

import string
import sys
import time
import binascii
from optparse import OptionParser

# Import Serial
try:
	import serial
except ImportError:
	print "Error: You need to install Serial extension for Python"
	sys.exit(1)

sw_name = "RFXCMD"
sw_version = "0.1f"
		
# ----------------------------------------------------------------------------
# Read x amount of bytes from serial port
# Boris Smus http://smus.com

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

def ByteToHex( byteStr ):
	return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()

# ----------------------------------------------------------------------------
# Return the binary representation of dec_num
# http://code.activestate.com/recipes/425080-easy-binary2decimal-and-decimal2binary/
# Guyon Mor�e http://gumuz.looze.net/

def Decimal2Binary(dec_num):
	if dec_num == 0: return '0'
	return (Decimal2Binary(dec_num >> 1) + str(dec_num % 2))

# ----------------------------------------------------------------------------
# testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
# http://wiki.python.org/moin/BitManipulation

def testBit(int_type, offset):
	mask = 1 << offset
	return(int_type & mask)

# ----------------------------------------------------------------------------
# clearBit() returns an integer with the bit at 'offset' cleared.
# http://wiki.python.org/moin/BitManipulation

def clearBit(int_type, offset):
	mask = ~(1 << offset)
	return(int_type & mask)

# ----------------------------------------------------------------------------
# split_len, split string into specified chunks

def split_len(seq, length):
	return [seq[i:i+length] for i in range(0, len(seq), length)]

# ----------------------------------------------------------------------------
# Decode packet

def decodePacket( message ):
	
	decoded = False
	db = ""
	
	packettype = ByteToHex(message[1])
	subtype = ByteToHex(message[2])
	seqnbr = ByteToHex(message[3])
	id1 = ByteToHex(message[4])
	id2 = ByteToHex(message[5])
	
	if printout_complete == True:
		print "Packettype\t\t= " + rfx_packettype[packettype]
	
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
	# 0x50 - Temperature sensors
	# ---------------------------------------
	if packettype == '50':
	
		decoded = True
		temp_high = ByteToHex(message[6])
		temp_low = ByteToHex(message[7])
		
		polarity = testBit(int(temp_high,16),7)
		if polarity == 1:
			polarity_sign = "-"
		else:
			polarity_sign = ""

		temp_high = clearBit(int(temp_high,16),7)
		temp_high = temp_high << 8
		temperature = ( temp_high + int(temp_low,16) ) * 0.1
		temperature_str = polarity_sign + str(temperature)

		batt_rssi = ByteToHex(message[8])		
		battery = int(batt_rssi,16) >> 4
		signal = int(batt_rssi,16) & 0xf
		
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

				db = MySQLdb.connect(mysql_server, mysql_username, mysql_password, mysql_database)
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
	# 0x52 - Temperature and humidity sensors
	# ---------------------------------------
	if packettype == '52':
		
		decoded = True

		# Temperature
		temp_high = ByteToHex(message[6])
		temp_low = ByteToHex(message[7])
		polarity = testBit(int(temp_high,16),7)
		
		if polarity == 1:
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
		battery = int(batt_rssi,16) >> 4
		signal = int(batt_rssi,16) & 0xf
		
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
				db = MySQLdb.connect(mysql_server, mysql_username, mysql_password, mysql_database)
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
					
	# 0x52 END
	# ---------------------------------------
		
	# The packet is not decoded, then print it on the screen
	if decoded == False:
		print timestamp + " " + ByteToHex(message)
		print "RFXCMD does not hanlde this message, see readme.txt for more information."

	# decodePackage END
	return

# ----------------------------------------------------------------------------
# Responses

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
				"01":"Interface Message",
				"02":"Receiver/Transmitter Message",
				"03":"Undecoded RF Message",
				"10":"Lighting1",
				"11":"Lighting2",
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
					
rfx_subtype_02_msg1 = {"00":"",
						"01":"",
						"02":"",
						"03":""}

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

rfx_subtype_11 = {"00":"AC",
					"01":"HomeEasy EU",
					"02":"Anslut"}

rfx_subtype_14 = {"00":"LightwaveRF, Siemens",
					"01":"EMW100 GAO/Everflourish"}
					
rfx_subtype_15 = {"00":"Blyss"}

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

rfx_subtype_50 = {"01":"THR128/138, THC138 (TEMP1)",
					"02":"THC238/268,THN132,THWR288,THRN122,THN122,AW129/131 (TEMP1)",
					"03":"THWR800 (TEMP3)",
					"04":"RTHN318 (TEMP4)",
					"05":"La Crosse TX3, TX4, TX17 (TEMP5)",
					"06":"TS15C (TEMP6)",
					"07":"Viking 02811 (TEMP7)",
					"08":"La Crosse WS2300 (TEMP8)",
					"09":"RUBiCSON (TEMP9)",
					"0A":"TFA 30.3133 (TEMP10)"}

rfx_subtype_51 = {"01":"LaCrosse TX3 (HUM1)",
					"02":"LaCrosse WS2300 (HUM2)"}

rfx_subtype_52 = {"01":"THGN122/123, THGN132, THGR122/228/238/268 (TH1)",
					"02":"THGR810, THGN800 (TH2)",
					"03":"RTGR328 (TH3)",
					"04":"THGR328 (TH4)",
					"05":"WTGR800 (TH5)",
					"06":"THGR918, THGRN228, THGN500 (TH6)",
					"07":"TFA TS34C, Cresta (TH7)",
					"08":"WT260,WT260H,WT440H,WT450,WT450H (TH8)",
					"09":"Viking 02035, 02038 (TH9)"}

rfx_subtype_53 = {"01":"Reserved for future use"}

rfx_subtype_54 = {"01":"BTHR918 (THB1)",
					"02":"BTHR918N, BTHR968"}
					
rfx_subtype_55 = {"01":"RGR126/682/918 (RAIN1)",
					"02":"PCR800 (RAIN2)",
					"03":"TFA (RAIN3)",
					"04":"UPM RG700 (RAIN4)",
					"05":"WS2300 (RAIN5)"}
					
rfx_subtype_56 = {"01":"WTGR800 (WIND1)",
					"02":"WGR800 (WIND2)",
					"03":"STR918, WGR918 (WIND3)",
					"04":"TFA (WIND4)",
					"05":"UPM WDS500 (WIND5)",
					"06":"WS2300 (WIND6)"}

rfx_subtype_57 = {"01":"UVN128, UV138 (UV1)",
					"02":"UVN800 (UV2)",
					"03":"TFA (UV3)"}
					
rfx_subtype_58 = {"01":"RTGR328N (DT1)"}

rfx_subtype_59 = {"01":"CM113, Electrisave (ELEC1)"}

rfx_subtype_5A = {"01":"CM119/160 (ELEC2)"}

rfx_subtype_5D = {"01":"BWR101/102 (WEIGHT1)",
					"02":"GR101 (WEIGHT2)"}
					
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
# Commands

rfx_reset="0d00000000000000000000000000"
rfx_getstatus="0d00000002000000000000000000"

# ----------------------------------------------------------------------------
# Printout types

printout_complete = True
printout_csv = False

# Check current Python version
if sys.hexversion < 0x02060000:
	print "Error: Your Python need to be 2.6 or newer, please upgrade."
	exit()

# Parse command line arguments
parser = OptionParser()
parser.add_option("-d", "--device", action="store", type="string", dest="device", help="The serial device of the RFXCOM, example /dev/ttyUSB0")
parser.add_option("-a", "--action", action="store", type="string", dest="action", help="Specify which action: LISTEN (default), STATUS")
parser.add_option("-x", "--simulate", action="store", type="string", dest="indata", help="Simulate one incoming data string")
parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, help="Output data in CSV format")
parser.add_option("-m", "--mysql", action="store_true", dest="mysql", default=False, help="Insert data to MySQL database")
parser.add_option("-s", "--server", action="store", type="string", dest="server", help="MySQL server address, default : localhost")
parser.add_option("-b", "--database", action="store", type="string", dest="database", help="MySQL database, default : rfxcmd")
parser.add_option("-u", "--username", action="store", type="string", dest="username", help="MySQL username")
parser.add_option("-p", "--password", action="store", type="string", dest="password", help="MySQL password")

(options, args) = parser.parse_args()

if options.csv:
	printout_complete = False
	printout_csv = True

if options.mysql:
	printout_complete = False
	printout_csv = False

if printout_complete == True:
	print sw_name + " version " + sw_version

if options.mysql == True:

	# Import MySQLdb
	try:
		import MySQLdb
	except ImportError:
		print "Error: You need to install MySQL extension for Python"
		sys.exit(1)
		
	# MySQL Server
	if options.server:
		mysql_server = options.server
	else:
		mysql_server = "localhost"

	# MySQL Database
	if options.database:
		mysql_database = options.database
	else:
		mysql_database = "rfxcmd"
	
	# MySQL Username
	if options.username:
		mysql_username = options.username
	else:
		parser.error('MySQL Username is missing')

	# MySQL Password
	if options.password:
		mysql_password = options.password
	else:
		parser.error('MySQL Password is missing')
		
else:

	if options.server:
		parser.error('The -m argument is missing')
	if options.database:
		parser.error('The -m argument is missing')
	if options.username:
		parser.error('The -m argument is missing')
	if options.password:
		parser.error('The -m argument is missing')

if options.action:
	rfxcmd_action = options.action.lower()
	if not (rfxcmd_action == "listen" or rfxcmd_action == "status"):
		parser.error('Invalid action')
else:
	rfxcmd_action = "listen"

# ----------------------------------------------------------------------------
# SIMULATE
# ----------------------------------------------------------------------------

if options.indata:
	indata=options.indata
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
	
	exit()

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
# LISTEN TO RFXCOM
# ----------------------------------------------------------------------------

if rfxcmd_action == "listen":

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	# Send RESET
	serialport.write( rfx_reset.decode('hex') )
	time.sleep(1)

	# Flush buffer
	serialport.flushOutput()
	serialport.flushInput()

	# Send GET STATUS
	serialport.write( rfx_getstatus.decode('hex') )
	time.sleep(1)

	try:
		while 1:
			byte = serialport.read()
			if byte:
				message = byte + readbytes( ord(byte) )
			
				if ByteToHex(message[0]) <> "00":
			
					timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
					if printout_complete == True:
						print "------------------------------------------------"
						print "Received\t\t= " + ByteToHex(message)
						print "Date/Time\t\t= " + timestamp
						print "Packet Length\t\t= " + ByteToHex(message[0])
				
					decodePacket( message )
			
	except KeyboardInterrupt:
		print "\nExit..."
		pass

# ----------------------------------------------------------------------------
# GET RFXCOM STATUS
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

	# Send GET STATUS
	serialport.write( rfx_getstatus.decode('hex') )
	time.sleep(1)

	byte = serialport.read()
	if byte:
		message = byte + readbytes( ord(byte) )
			
		if ByteToHex(message[0]) <> "00":
			
			timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
			if printout_complete == True:
				print "------------------------------------------------"
				print "Received\t\t= " + ByteToHex(message)
				print "Date/Time\t\t= " + timestamp
				print "Packet Length\t\t= " + ByteToHex(message[0])
				
				decodePacket( message )

# ----------------------------------------------------------------------------
# CLOSE SERIAL CONNECTION
# ----------------------------------------------------------------------------

try:
	serialport.close()
except:
	print "Error: Failed to close the port " + device

exit()