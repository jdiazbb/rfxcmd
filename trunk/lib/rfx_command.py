#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#	
#	RFX_COMMAND.PY
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
#	$Rev: 464 $
#	$Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
# ------------------------------------------------------------------------------

# --------------------------------------------------------------------------

import logging
import subprocess
import threading

logger = logging.getLogger('rfxcmd')

class Command(object):
	def __init__(self, cmd):
		self.cmd = cmd
		self.process = None
	
	def run(self, timeout):
		def target():
			logger.debug("Thread started")
			self.process = subprocess.Popen(self.cmd, shell=True)
			self.process.communicate()
			logger.debug("Thread finished")
		
		thread = threading.Thread(target=target)
		thread.start()

		"""
		thread.join(timeout)
		if thread.is_alive():
			logger.debug("Terminating process")
			self.process.terminate()
			thread.join()
		"""
        
        #logger.debug("Return code: " + str(self.process.returncode))

# ----------------------------------------------------------------------------
