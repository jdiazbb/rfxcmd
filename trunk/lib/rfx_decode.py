#!/usr/bin/python
# coding=UTF-8

import time
import logging

logger = logging.getLogger('rfxcmd')

def stripped(str):
	"""
	Strip all characters that are not valid
	Credit: http://rosettacode.org/wiki/Strip_control_codes_and_extended_characters_from_a_string
	"""
	return "".join([i for i in str if ord(i) in range(32, 127)])

def ByteToHex( byteStr ):
	"""
	Convert a byte string to it's hex string representation e.g. for output.
	http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/

	Added str() to byteStr in case input data is in integer
	"""	
	return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()
	
def test_rfx( message ):
	"""
	Test, filter and verify that the incoming message is valid
	Return true if valid, False if not
	"""
		
	# Remove all invalid characters
	message = stripped(message)
	
	# Remove any whitespaces
	try:
		message = message.replace(' ', '')
	except Exception:
		logger.debug("Error: Removing white spaces")
		return False
	
	# Test the string if it is hex format
	try:
		int(message,16)
	except Exception:
		logger.debug("Error: Packet not hex format")
		return False
	
	# Check that length is even
	if len(message) % 2:
		logger.debug("Error: Packet length not even")
		return False
	
	# Check that first byte is not 00
	if ByteToHex(message.decode('hex')[0]) == "00":
		logger.debug("Error: Packet first byte is 00")
		return False
	
	# Length more than one byte
	if not len(message.decode('hex')) > 1:
		logger.debug("Error: Packet is not longer than one byte")
		return False
	
	# Check if string is the length that it reports to be
	cmd_len = int( ByteToHex( message.decode('hex')[0]),16 )
	if not len(message.decode('hex')) == (cmd_len + 1):
		logger.debug("Error: Packet length is not valid")
		return False

	logger.debug("Test packet: " + message)

	return True

def decodePacket(message):
	"""
	Decode incoming RFXtrx message.
	"""
	
	timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
	unixtime_utc = int(time.time())

	decoded = False
	db = ""
	
	# Verify incoming message
	if not test_rfx( ByteToHex(message) ):
		if cmdarg.printout_complete == True:
			print "Error: The incoming message is invalid"
			return
			
	packettype = ByteToHex(message[1])

	if len(message) > 2:
		subtype = ByteToHex(message[2])
	
	if len(message) > 3:
		seqnbr = ByteToHex(message[3])

	if len(message) > 4:
		id1 = ByteToHex(message[4])
	
	if len(message) > 5:
		id2 = ByteToHex(message[5])
	
	if cmdarg.printout_complete:
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
		
		if cmdarg.printout_complete:
			
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
			sys.stdout.flush()
			
		# MYSQL
		if config.mysql_active:
			if subtype == '00':
				insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			else:
				insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, str(id1), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			if subtype == '00':
				insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			else:
				insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, str(id1), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

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
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_03[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Message\t\t\t= " + indata

		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, indata ))
			sys.stdout.flush()
			
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, indata, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, indata, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x10 Lighting1
	# ---------------------------------------
	if packettype == '10':

		decoded = True
		
		# DATA
		housecode = rfx.rfx_subtype_10_housecode[ByteToHex(message[4])]
		unitcode = int(ByteToHex(message[5]), 16)
		command = rfx.rfx_subtype_10_cmnd[ByteToHex(message[6])]
		signal = decodeSignal(message[7])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_10[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Housecode\t\t= " + housecode
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), housecode, command, str(unitcode) ))
			sys.stdout.flush()
		
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, housecode, 0, command, unitcode, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, housecode, 0, command, unitcode, 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x11 Lighting2
	# ---------------------------------------
	if packettype == '11':

		decoded = True
		
		# DATA
		sensor_id = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6]) + ByteToHex(message[7])
		unitcode = int(ByteToHex(message[8]),16)
		command = rfx.rfx_subtype_11_cmnd[ByteToHex(message[9])]
		dimlevel = rfx.rfx_subtype_11_dimlevel[ByteToHex(message[10])]
		signal = decodeSignal(message[11])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_11[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			print "Dim level\t\t= " + dimlevel + "%"
			print "Signal level\t\t= " + str(signal)
		
		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), sensor_id, command, str(unitcode), dimlevel ))
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, command, unitcode, int(dimlevel), 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, command, unitcode, int(dimlevel), 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x12 Lighting3
	# ---------------------------------------
	if packettype == '12':

		decoded = True
		
		# DATA
		system = ByteToHex(message[4])

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

		command = rfx.rfx_subtype_12_cmnd[ByteToHex(message[7])]
		battery = decodeBattery(message[8])
		signal = decodeSignal(message[8])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_12[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "System\t\t\t= " + system
			print "Channel\t\t\t= " + str(channel)
			print "Command\t\t\t= " + command
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV 
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;\n" %(timestamp, packettype, subtype, seqnbr, str(battery), str(signal), str(system), command, str(channel) ))
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, str(system), 0, command, str(channel), 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, str(system), 0, command, str(channel), 0, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x13 Lighting4
	# ---------------------------------------
	if packettype == '13':

		decoded = True

		# DATA
		code = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
		code1 = dec2bin(int(ByteToHex(message[4]),16))
		code2 = dec2bin(int(ByteToHex(message[5]),16))
		code3 = dec2bin(int(ByteToHex(message[6]),16))
		code_bin = code1 + " " + code2 + " " + code3
		pulse = ((int(ByteToHex(message[7]),16) * 256) + int(ByteToHex(message[8]),16))
		signal = decodeSignal(message[9])		
		
		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_13[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Code\t\t\t= " + code
			print "S1-S24\t\t\t= "  + code_bin
			print "Pulse\t\t\t= " + str(pulse) + " usec"
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, code, code_bin, str(pulse), str(signal) ))
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x14 Lighting5
	# ---------------------------------------
	if packettype == '14':

		decoded = True
		
		# DATA
		sensor_id = id1 + id2 + ByteToHex(message[6])
		unitcode = int(ByteToHex(message[7]),16)
		
		if subtype == '00':
			command = rfx.rfx_subtype_14_cmnd0[ByteToHex(message[8])]
		elif subtype == '01':
			command = rfx.rfx_subtype_14_cmnd1[ByteToHex(message[8])]
		elif subtype == '02':
			command = rfx.rfx_subtype_14_cmnd2[ByteToHex(message[8])]
		else:
			command = "Unknown"
		
		if subtype == "00":
			level = ByteToHex(message[9])
		else:
			level = 0
		
		signal = decodeSignal(message[10])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_14[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			
			if subtype == '00':
				print "Level\t\t\t= " + level
			
			print "Signal level\t\t= " + str(signal)
	
		# CSV
		if cmdarg.printout_csv:
			if subtype == '00':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(unitcode), command, level, str(signal) ))
			else:
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(unitcode), command, str(signal) ))
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, sensor_id, 0, command, str(unitcode), level, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, sensor_id, 0, command, str(unitcode), level, 0, 0, 0, 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x15 Lighting6
	# Credit: Dimitri Clatot
	# ---------------------------------------
	if packettype == '15':

		decoded = True

		# DATA
		sensor_id = id1 + id2
		groupcode = rfx.rfx_subtype_15_groupcode[ByteToHex(message[6])]
		unitcode = int(ByteToHex(message[7]),16)
		command = rfx.rfx_subtype_15_cmnd[ByteToHex(message[8])]
		command_seqnbr = ByteToHex(message[9])
		signal = decodeSignal(message[11])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_15[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "ID\t\t\t= "  + sensor_id
			print "Groupcode\t\t= " + groupcode
			print "Unitcode\t\t= " + str(unitcode)
			print "Command\t\t\t= " + command
			print "Command seqnbr\t\t= " + command_seqnbr
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(signal), groupcode, command, str(unitcode), str(command_seqnbr) ))
			sys.stdout.flush()
			
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, groupcode, command, unitcode, command_seqnbr, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, groupcode, command, unitcode, command_seqnbr, 0, 0, 0, 0, 0, 0, 0, 0)

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x18 Curtain1 (Transmitter only)
	# ---------------------------------------
	if packettype == '18':

		decoded = True

		# PRINTOUT		
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_18[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x19 Blinds1
	# ---------------------------------------
	if packettype == '19':

		decoded = True
		
		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_19[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x20 Security1
	# Credit: Dimitri Clatot
	# ---------------------------------------
	if packettype == '20':

		decoded = True
		
		# DATA
		sensor_id = id1 + id2 + ByteToHex(message[6])
		status = rfx.rfx_subtype_20_status[ByteToHex(message[7])]
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
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id, status ) )
			sys.stdout.flush()
			
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, status, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, status, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x28 Camera1
	# ---------------------------------------
	if packettype == '28':

		decoded = True
		
		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_28[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com"

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

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
		if cmdarg.printout_complete:
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
		if cmdarg.printout_csv:
			if subtype == '00' or subtype == '02':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, command))
			elif subtype == '04' or subtype == '01' or subtype == '03':
				command = "Not implemented in RFXCMD"
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			if subtype == '00' or subtype == '02':
				insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, id1, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			elif subtype == '04' or subtype == '01' or subtype == '03':
				command = "Not implemented in RFXCMD"

		# SQLITE
		if config.sqlite_active:
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

		# DATA
		sensor_id = id1 + id2
		temperature = int(ByteToHex(message[6]), 16)
		temperature_set = int(ByteToHex(message[7]), 16)
		status_temp = str(testBit(int(ByteToHex(message[8]),16),0) + testBit(int(ByteToHex(message[8]),16),1))
		status = rfx.rfx_subtype_40_status[status_temp]
		if testBit(int(ByteToHex(message[8]),16),7) == 128:
			mode = rfx.rfx_subtype_40_mode['1']
		else:
			mode = rfx.rfx_subtype_40_mode['0']
		signal = decodeSignal(message[9])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_40[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Temperature\t\t= " + str(temperature) + " C"
			print "Temperature set\t\t= " + str(temperature_set) + " C"
			print "Mode\t\t\t= " + mode
			print "Status\t\t\t= " + status
			print "Signal level\t\t= " + str(signal)

		# CSV 
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), mode, status, str(temperature_set), str(temperature) ))
			sys.stdout.flush()
	
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$temperature$", str(temperature) )
					action = action.replace("$temperatureset$", str(temperature_set) )
					action = action.replace("$mode$", mode )
					action = action.replace("$status$", status )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, mode, status, 0, 0, 0, temperature_set, temperature, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, mode, status, 0, 0, 0, temperature_set, temperature, 0, 0, 0, 0, 0)

		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=temperature\ncurrent='+temperature+'\nunits=C')
			xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=temperature_set\ncurrent='+temperature_set+'\nunits=C')
			xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=mode\ncurrent='+mode+'\n')
			xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=status\ncurrent='+mode+'\n')
			xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x41 Thermostat2
	# ---------------------------------------
	if packettype == '41':

		decoded = True
		
		# PRINTOUT		
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_41[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			# TODO

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x42 Thermostat3
	# ---------------------------------------
	if packettype == '42':

		decoded = True

		# DATA
		if subtype == '00':
			unitcode = ByteToHex(message[4])
		elif subtype == '01':
			unitcode = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
		else:
			unitcode = "00"

		if subtype == '00':
			command = rfx.rfx_subtype_42_cmd00[ByteToHex(message[7])]
		elif subtype == '01':
			command = rfx.rfx_subtype_42_cmd01[ByteToHex(message[7])]
		else:
			command = '0'

		signal = decodeSignal(message[8])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_42[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Unitcode\t\t\t= " + unitcode
			print "Command\t\t\t= " + command
			print "Signal level\t\t= " + str(signal)

		# CSV 
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %(timestamp, packettype, subtype, seqnbr, str(signal), unitcode, command))
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, unitcode, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_config:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, unitcode, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Thermostat.'+unitcode+'\ntype=command\ncurrent='+command+'\nunits=C')
			xpl.send(config.xpl_host, 'device=Thermostat.'+unitcode+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x50 - Temperature sensors
	# ---------------------------------------
	if packettype == '50':
	
		decoded = True

		# DATA
		sensor_id = id1 + id2
		temperature = decodeTemperature(message[6], message[7])
		signal = decodeSignal(message[8])
		battery = decodeBattery(message[8])

		# PRINTOUT
		if cmdarg.printout_complete:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_50[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Temperature\t\t= " + temperature + " C"
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, str(battery), str(signal), temperature ))
			sys.stdout.flush()
			
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$temperature$", str(temperature) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Temp.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C')
			xpl.send(config.xpl_host, 'device=Temp.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Temp.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x51 - Humidity sensors
	# ---------------------------------------

	if packettype == '51':
		
		decoded = True

		# DATA
		sensor_id = id1 + id2
		humidity = int(ByteToHex(message[6]),16)
		humidity_status = rfx.rfx_subtype_51_humstatus[ByteToHex(message[7])]
		signal = decodeSignal(message[8])
		battery = decodeBattery(message[8])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_51[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "Humidity\t\t= " + str(humidity)
			print "Humidity Status\t\t= " + humidity_status
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)
		
		# CSV
		if cmdarg.printout_csv:
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, humidity_status, str(humidity), str(battery), str(signal)) )
			sys.stdout.flush()
		
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$humidity$", str(humidity) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, 0, 0, 0, 0, 0, 0)

		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Hum.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Hum.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Hum.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x52 - Temperature and humidity sensors
	# ---------------------------------------
	if packettype == '52':
		
		logger.debug("PacketType 0x52")

		decoded = True

		# DATA
		sensor_id = id1 + id2
		temperature = decodeTemperature(message[6], message[7])
		humidity = int(ByteToHex(message[8]),16)
		humidity_status = rfx.rfx_subtype_52_humstatus[ByteToHex(message[9])]
		signal = decodeSignal(message[10])
		battery = decodeBattery(message[10])
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			logger.debug("Print data stdout")
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
			logger.debug("CSV Output")
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, humidity_status,
							temperature, str(humidity), str(battery), str(signal)) )
			sys.stdout.flush()
		
		# TRIGGER
		if config.trigger:
			logger.debug("Check trigger")			
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					logger.debug("Trigger match")
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$temperature$", str(temperature) )
					action = action.replace("$humidity$", str(humidity) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		# GRAPHITE
		if config.graphite_active == True:
			logger.debug("Send to Graphite")
			now = int( time.time() )
			linesg=[]
			linesg.append("%s.%s.temperature %s %d" % ( 'rfxcmd', sensor_id, temperature,now))
			linesg.append("%s.%s.humidity %s %d" % ( 'rfxcmd', sensor_id, humidity,now))
			linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
			linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
			send_graphite(config.graphite_server, config.graphite_port, linesg)

		# MYSQL
		if config.mysql_active:
			logger.debug("Send to MySQL")
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			logger.debug("Send to Sqlite")
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# XPL
		if config.xpl_active:
			logger.debug("Send to xPL")
			xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C')
			xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x53 - Barometric
	# RESERVED FOR FUTURE
	# ---------------------------------------

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
							forecast, humidity_status, str(humidity), str(barometric), str(temperature)))
			sys.stdout.flush()
		
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$temperature$", str(temperature) )
					action = action.replace("$humidity$", str(humidity) )
					action = action.replace("$baromatric$", str(baromatric) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, forecast, humidity_status, humidity, barometric, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, forecast, humidity_status, humidity, barometric, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C')
			xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=humidity\ncurrent='+str(barometric)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

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
			sys.stdout.flush()
		
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		"""			
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)
		"""

	# ---------------------------------------
	# 0x56 - Wind sensors
	# ---------------------------------------
	if packettype == '56':
		
		decoded = True

		# DATA
		sensor_id = id1 + id2
		direction = ( ( int(ByteToHex(message[6]),16) * 256 ) + int(ByteToHex(message[7]),16) )
		if subtype <> "05":
			av_speed = ( ( int(ByteToHex(message[8]),16) * 256 ) + int(ByteToHex(message[9]),16) ) * 0.1
		else:
			av_speed = 0;
		gust = ( ( int(ByteToHex(message[10]),16) * 256 ) + int(ByteToHex(message[11]),16) ) * 0.1
		if subtype == "04":
			temperature = decodeTemperature(message[12], message[13])
		else:
			temperature = 0
		if subtype == "04":
			windchill = decodeTemperature(message[14], message[15])
		else:
			windchill = 0
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
			sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
							(timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id, str(temperature), str(av_speed), str(gust), str(direction), str(windchill) ) )
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$direction$", str(direction) )
					if subtype <> "05":
						action = action.replace("$average$", str(av_speed) )
					if subtype == "04":
						action = action.replace("$temperature$", str(temperature) )
						action = action.replace("$windchill$", str(windchill) )
					action = action.replace("$windgust$", str(windgust) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)
		
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)

		# xPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=direction\ncurrent='+str(direction)+'\nunits=Degrees')
			
			if subtype <> "05":
				xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=Averagewind\ncurrent='+str(av_speed)+'\nunits=mtr/sec')
			
			if subtype == "04":
				xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=temperature\ncurrent='+str(temperature)+'\nunits=C')
				xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=windchill\ncurrent='+str(windchill)+'\nunits=C')
			
			xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=windgust\ncurrent='+str(gust)+'\nunits=mtr/sec')
			xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x57 UV Sensor
	# ---------------------------------------

	if packettype == '57':

		decoded = True

		# DATA
		sensor_id = id1 + id2
		uv = int(ByteToHex(message[6]), 16) * 10
		temperature = decodeTemperature(message[6], message[8])
		signal = decodeSignal(message[9])
		battery = decodeBattery(message[9])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_57[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + sensor_id
			print "UV\t\t\t= " + str(uv)
			if subtype == '03':
				print "Temperature\t\t= " + temperature + " C"
			print "Battery\t\t\t= " + str(battery)
			print "Signal level\t\t= " + str(signal)

		# CSV
		if cmdarg.printout_csv:
			if subtype == '03':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(uv), temperature, str(battery), str(signal) ) )
			else:
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(uv), str(battery), str(signal) ) )
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					action = action.replace("$uv$", str(temperature) )
					if subtype == '03':
						action = action.replace("$temperature$", str(humidity) )
					action = action.replace("$battery$", str(battery) )
					action = action.replace("$signal$", str(signal) )
					return_code = subprocess.call(action, shell=True)

		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, str(uv), 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, str(uv), 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)

		# xPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=UV.'+sensor_id+'\ntype=uv\ncurrent='+str(uv)+'\nunits=Index')
			if subtype == "03":
				xpl.send(config.xpl_host, 'device=UV.'+sensor_id+'\ntype=Temperature\ncurrent='+str(temperature)+'\nunits=Celsius')

	# ---------------------------------------
	# 0x59 Current Sensor
	# ---------------------------------------

	if packettype == '59':

		decoded = True

		# DATA
		sensor_id = id1 + id2
		count = int(ByteToHex(message[6]),16)
		channel1 = (int(ByteToHex(message[7]),16) * 0x100 + int(ByteToHex(message[8]),16)) * 0.1
		channel2 = int(ByteToHex(message[9]),16) * 0x100 + int(ByteToHex(message[10]),16)
		channel3 = int(ByteToHex(message[11]),16) * 0x100 + int(ByteToHex(message[12]),16)
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
	
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel1\ncurrent='+str(channel1)+'\nunits=A')
			xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel2\ncurrent='+str(channel2)+'\nunits=A')
			xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel3\ncurrent='+str(channel3)+'\nunits=A')
			xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x5A Energy sensor
	# Credit: Jean-Michel ROY
	# ---------------------------------------
	if packettype == '5A':

		decoded = True

		# DATA
		sensor_id = id1 + id2
		signal = decodeSignal(message[17])
		battery = decodeBattery(message[17])
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
			sys.stdout.flush()
		
		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
		
		# XPL
		if config.xpl_active:
			xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=instant_usage\ncurrent='+str(instant)+'\nunits=W')
			xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=total_usage\ncurrent='+str(usage)+'\nunits=Wh')
			xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%')
			xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%')

	# ---------------------------------------
	# 0x5B Current + Energy sensor
	# ---------------------------------------
	
	if packettype == '58':

		decoded = True

		# DATA
		sensor_id = id1 + id2
		date_year = ByteToHex(message[6]);
		date_month = ByteToHex(message[7]);
		date_day = ByteToHex(message[8]);
		date_dow = ByteToHex(message[9]);
		time_hour = ByteToHex(message[10]);
		time_min = ByteToHex(message[11]);
		time_sec = ByteToHex(message[12]);
		signal = decodeSignal(message[13])
		battery = decodeBattery(message[13])

		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_58[subtype]
			print "Not implemented in RFXCMD, please send sensor data to sebastian.sjoholm@gmail.com"

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x70 RFXsensor
	# ---------------------------------------
	if packettype == '70':

		decoded = True

		# DATA
		if subtype == '00':
			temperature = float(decodeTemperature(message[5], message[6]))
			temperature = temperature * 0.1
		else:
			temperature = 0
		if subtype == '01' or subtype == '02':
			voltage_hi = int(ByteToHex(message[5]), 16) * 256
			voltage_lo = int(ByteToHex(message[6]), 16)
			voltage = voltage_hi + voltage_lo
		else:
			voltage = 0
		signal = decodeSignal(message[7])

		# PRINTOUT
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
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, str(temperature)))
			if subtype == '01' or subtype == '02':
				sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, str(voltage)))
			sys.stdout.flush()

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)
					
		# MYSQL
		if config.mysql_active:
			insert_mysql(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, id1, ByteToHex(message[5]), ByteToHex(message[6]), 0, 0, 0, voltage, float(temperature), 0, 0, 0, 0, 0)

		# SQLITE
		if config.sqlite_active:
			insert_sqlite(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, id1, ByteToHex(message[5]), ByteToHex(message[6]), 0, 0, 0, voltage, float(temperature), 0, 0, 0, 0, 0)

	# ---------------------------------------
	# 0x71 RFXmeter
	# ---------------------------------------
	if packettype == '71':

		decoded = True
		
		# DATA
		sensor_id = id1 + id2
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_70[subtype]
			print "Seqnbr\t\t\t= " + seqnbr
			print "Id\t\t\t= " + id1

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# 0x72 FS20
	# ---------------------------------------
	if packettype == '72':
	
		logger.debug("PacketType 0x72")

		decoded = True
		
		# PRINTOUT
		if cmdarg.printout_complete == True:
			print "Subtype\t\t\t= " + rfx.rfx_subtype_70[subtype]
			print "Not implemented in RFXCMD, please send sensor data to sebastian.sjoholm@gmail.com"

		# TRIGGER
		if config.trigger:
			for trigger in triggerlist.data:
				trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
				action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
				rawcmd = ByteToHex ( message )
				rawcmd = rawcmd.replace(' ', '')
				if re.match(trigger_message, rawcmd):
					action = action.replace("$id$", str(sensor_id) )
					return_code = subprocess.call(action, shell=True)

	# ---------------------------------------
	# Not decoded message
	# ---------------------------------------	
	
	# The packet is not decoded, then print it on the screen
	if decoded == False:
		logger.debug("Packet not decoded")
		print timestamp + " " + ByteToHex(message)
		print "RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/ for more information."

	# decodePackage END
	return

# ----------------------------------------------------------------------------
