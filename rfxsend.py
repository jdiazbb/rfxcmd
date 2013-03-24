#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#	
#	RFXSEND.PY
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
#	Website: http://code.google.com/p/rfxcmd/
#
#	$Rev: 360 $
#	$Date: 2013-03-23 23:30:58 +0100 (Sat, 23 Mar 2013) $
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
__version__ = "0.1 (" + filter(str.isdigit, "$Rev: 360 $") + ")"
__maintainer__ = "Sebastian Sjoholm"
__email__ = "sebastian.sjoholm@gmail.com"
__status__ = "Development"
__date__ = "$Date: 2013-03-23 23:30:58 +0100 (Sat, 23 Mar 2013) $"

# Default modules
import sys
import string
import socket
import optparse
import rfxcmd

# -----------------------------------------------------------------------------

def print_version():
	"""
	Print RFXSEND version, build and date
	"""
 	print "RFXSEND Version: " + __version__
 	print __date__.replace('$', '')
 	sys.exit(0)

# -----------------------------------------------------------------------------

def rfx_send(socket_server, socket_port, message):
	"""
	Send message to the RFXCMD socket server
	
	Input:
	- socket_server = IP address at RFXCMD
	- socket_port = socket port at RFXCMD
	- message = raw RFX message to be sent
	
	Output: None
	
	"""
	sock = None
	
	try:
		sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	except socket.error as msg:
		sock = None
		
	try:
		sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
	except socket.error as msg:
		sock.close()
		sock = None

	sock.sendto(message,(socket_server,socket_port))

# -----------------------------------------------------------------------------

if __name__ == '__main__':

	parser = optparse.OptionParser()
	parser.add_option("-s", "--server", action="store", type="string", dest="server", help="IP address of the RFXCMD server (default: localhost)")
	parser.add_option("-p", "--port", action="store", type="string", dest="port", help="Port of the RFXCMD server (default: 50000)")
	parser.add_option("-r", "--rawcmd", action="store", type="string", dest="rawcmd", help="The raw message to be sent")
	parser.add_option("-v", "--version", action="store_true", dest="version", help="Print rfxcmd version information")

	(options, args) = parser.parse_args()

	if options.version:
		print_version()

	if options.server:
		socket_server = options.server
	else:
		socket_server = 'localhost'

	if options.port:
		socket_port = options_port
	else:
		socket_port = 50000
	
	if options.rawcmd:
		if rfxcmd.test_rfx(options.rawcmd):
			message = options.rawcmd
		else:
			print "Error: rawcmd message is invalid"
			sys.exit(1)
	else:
		print "Error: rawcmd message is missing"
		sys.exit(1)
	
	rfx_send(socket_server, socket_port, message)
	
	sys.exit(0)

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
