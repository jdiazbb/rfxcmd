#!/usr/bin/python
# coding=UTF-8

import sys
import string
import socket

# -----------------------------------------------------------------------------

def rfx_send(message):

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

	sock.sendto(message,("localhost",50000))

if __name__ == '__main__':
	rfx_send("Test message to rfxcmd")