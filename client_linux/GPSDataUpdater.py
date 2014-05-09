#!/usr/bin/python

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# 
# Licensed under the GNU Public License, version 2.

import threading
import gps
import sys
import logging

class GPSDataUpdater(threading.Thread):
	def __init__(self):
		logging.debug("[%s]: Initializing GPSDataUpdater" % (__file__))

		threading.Thread.__init__(self)

		# initialize python gps modul
		try:
			self.session = gps.gps()
			self.session.next()
			self.session.stream()
		except:
			logging.warning("[%s]: Failed to initialize GPSDataUpdater" \
				% (__file__))
			return

		# set exit flag as false
		self.exitflag = False

		self.latitude = None
		self.longitude = None
		self.utctime = None
		self.altitude = None
		self.speed = None

		# initialize lock for data acess
		self.accessdatalock = threading.Semaphore(1)

		# set thread to daemon
		threading.daemon = True


	def run(self):
		logging.info("[%s]: Starting GPSDataUpdater" % (__file__))
		try:
			while 1:
				self.session.next()

				# lock for writing data
				self.accessdatalock.acquire()

				# Latitude in degrees: +/- signifies West/East
				self.latitude = self.session.fix.latitude
				# Longitude in degrees: +/- signifies North/South
				self.longitude = self.session.fix.longitude
				self.utctime = self.session.utc
				self.altitude = self.session.fix.altitude
				self.speed = self.session.fix.speed

				self.accessdatalock.release()

				# check exit flag and if set => exit
				if self.exitflag:
					logging.debug("[%s]: Quitting GPSDataUpdater" % (__file__))
					return
		except:
			logging.error("[%s]: Exception: %s" % (__file__, sys.exc_info()))
			return


	def getValues(self):

		# lock for reading data
		self.accessdatalock.acquire()

		latitude = self.latitude
		longitude = self.longitude
		altitude = self.altitude
		utctime = self.utctime
		speed = self.speed

		self.accessdatalock.release()

		return latitude, longitude, altitude, utctime, speed

	# sets the exit flag
	def exit(self):
		logging.debug("[%s]: Tell GPSDataUpdater to quit" % (__file__))
		self.exitflag = True
		return
