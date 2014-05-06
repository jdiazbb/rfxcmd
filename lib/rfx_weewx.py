#!/usr/bin/python
# -*- coding:utf-8 -*-
 
# ------------------------------------------------------------------------------
#	
#	RFX_WEEWX.PY
#	
#	Copyright (C) 2013 M. Bakker
#
#	Class weewx_data, needed for sending answer at request of 
#	WEEWX Weatherstation software
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
#	Website
#	http://code.google.com/p/rfxcmd/
#
#	$Rev: 464 $
#	$Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
# ------------------------------------------------------------------------------

# --------------------------------------------------------------------------

import logging

logger = logging.getLogger('rfxcmd')

class weewx_data:
	def __init__(
		self,
		wwx_wind_dir = 0,
		wwx_wind_avg = 0,
		wwx_wind_gust = 0,
		wwx_wind_batt = 0,
		wwx_wind_sign = 0,
		wwx_th_t_out = 0,
		wwx_th_h_out = 0,
		wwx_th_hs_out = 0,
		wwx_th_batt = 0,
		wwx_th_sign = 0,
		wwx_thb_t_in = 0,
		wwx_thb_h_in = 0,
		wwx_thb_hs_in = 0,
		wwx_thb_b_in = 0,
		wwx_thb_fs_in = 0,
		wwx_thb_batt = 0,
		wwx_thb_sign = 0,
		wwx_rain_rate = 0,
		wwx_rain_batt = 0,
		wwx_rain_sign = 0,
		wwx_uv_out = 0,
		wwx_uv_batt = 0,
		wwx_uv_sign = 0,
		wwx_0x57_uv = 0,
		wwx_0x57_temp = 0,
		wwx_0x57_batt = 0,
		wwx_0x57_rssi = 0
		):
		
		self.wwx_wind_dir = wwx_wind_dir
		self.wwx_wind_avg = wwx_wind_avg
		self.wwx_wind_gust = wwx_wind_gust
		self.wwx_wind_batt = wwx_wind_batt
		self.wwx_wind_sign = wwx_wind_sign
		self.wwx_th_t_out = wwx_th_t_out
		self.wwx_th_h_out = wwx_th_h_out
		self.wwx_th_hs_out = wwx_th_hs_out
		self.wwx_th_batt = wwx_th_batt
		self.wwx_th_sign = wwx_th_sign
		self.wwx_thb_t_in = wwx_thb_t_in
		self.wwx_thb_h_in = wwx_thb_h_in
		self.wwx_thb_hs_in = wwx_thb_hs_in
		self.wwx_thb_b_in = wwx_thb_b_in
		self.wwx_thb_fs_in = wwx_thb_fs_in
		self.wwx_thb_batt = wwx_thb_batt
		self.wwx_thb_sign = wwx_thb_sign
		self.wwx_rain_rate = wwx_rain_rate
		self.wwx_rain_batt = wwx_rain_batt
		self.wwx_rain_sign = wwx_rain_sign
		self.wwx_uv_out = wwx_uv_out
		self.wwx_uv_batt = wwx_uv_batt
		self.wwx_uv_sign = wwx_uv_sign
		
		# 0x57 UV Sensor
		self.wwx_0x57_uv = wwx_0x57_uv
		self.wwx_0x57_temp = wwx_0x57_temp
		self.wwx_0x57_batt = wwx_0x57_batt
		self.wwx_0x57_rssi = wwx_0x57_rssi
	
	def weewx_result(self):
		result = '|'
		result = result + str(wwx.wwx_wind_dir) + '|' + str(wwx.wwx_wind_avg) + '|' + str(wwx.wwx_wind_gust)
		result = result + '|' + str(wwx.wwx_wind_batt) + '|' + str(wwx.wwx_wind_sign)
		result = result + '|' + str(wwx.wwx_th_t_out) + '|' + str(wwx.wwx_th_h_out) + '|' + str(wwx.wwx_th_hs_out)
		result = result + '|' + str(wwx.wwx_th_batt) + '|' + str(wwx.wwx_th_sign)
		result = result + '|' + str(wwx.wwx_thb_t_in) + '|' + str(wwx.wwx_thb_h_in)
		result = result + '|' + str(wwx.wwx_thb_hs_in) + '|' + str(wwx.wwx_thb_b_in)
		result = result + '|' + str(wwx.wwx_thb_fs_in) + '|' + str(wwx.wwx_thb_batt) + '|' + str(wwx.wwx_thb_sign)
		result = result + '|' + str(wwx.wwx_rain_rate) + '|' + str(wwx.wwx_rain_batt) + '|' + str(wwx.wwx_rain_sign)
		result = result + '|' + str(wwx.wwx_uv_out) + '|' + str(wwx.wwx_uv_batt) + '|' + str(wwx.wwx_uv_sign)
		result = result + '|'
		return result
	
	# 0x57 UV Sensor
	def weewx_0x57(self):
		result = None
		result = "%s;%s;%s;%s" % (str(wwx.wwx_0x57_uv),str(wwx.wwx_0x57_temp),str(wwx.wwx_0x57_batt),str(wwx.wwx_0x57_rssi))
		logger.debug("Weewx.0x57=%s" % str(result))
		return result
	
wwx = weewx_data()

# --------------------------------------------------------------------------
