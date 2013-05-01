#!/usr/bin/python
# -*- coding:utf-8 -*-

# ------------------------------------------------------------------------------
#	
#	RFX_LOGGER.PY
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
#	$Rev: 365 $
#	$Date: 2013-03-24 12:58:25 +0100 (Sun, 24 Mar 2013) $
#
# ------------------------------------------------------------------------------

import os
import time
import logging
import xml.dom.minidom as minidom

# ----------------------------------------------------------------------------
def logger_init(configfile, name, debug):
	"""

	Init loghandler and logging
	
	Input: 
	
		- configfile = location of the config.xml
		- name	= name
		- debug = True will send log to stdout, False to file
		
	Output:
	
		- Returns logger handler
	
	"""
	program_path = os.path.dirname(os.path.realpath(__file__))
	dom = None
	
	if os.path.exists( os.path.join(program_path, "config.xml") ):

		# Read config file
		f = open(os.path.join(program_path, "config.xml"),'r')
		data = f.read()
		f.close()

		try:
			dom = minidom.parseString(data)
		except:
			print "Error: problem in the config.xml file, cannot process it"

		if dom:
		
			# Get loglevel from config file
			try:
				xmlTag = dom.getElementsByTagName( 'loglevel' )[0].toxml()
				loglevel = xmlTag.replace('<loglevel>','').replace('</loglevel>','')
			except:
				loglevel = "INFO"

			# Get logfile from config file
			try:
				xmlTag = dom.getElementsByTagName( 'logfile' )[0].toxml()
				logfile = xmlTag.replace('<logfile>','').replace('</logfile>','')
			except:
				logfile = os.path.join(program_path, "rfxcmd.log")

			loglevel = loglevel.upper()

			formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
	
			if debug:
				loglevel = "DEBUG"
				handler = logging.StreamHandler()
			else:
				handler = logging.FileHandler(logfile)
							
			handler.setFormatter(formatter)

			logger = logging.getLogger(name)
			logger.setLevel(loglevel)
			logger.addHandler(handler)
			
			return logger
	
# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
