#!/usr/bin/python

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# 
# Licensed under the GNU Public License, version 2.

import os
import time
import datetime
import sys
import math
import csv
import threading
import logging
from GPSDataUpdater import GPSDataUpdater
from GPSDataSubmitter import GPSDataSubmitter
import ctypes
import ConfigParser


# parse config file
try:
	config = ConfigParser.RawConfigParser(allow_no_value=False)

	if os.path.dirname(sys.argv[0]) == "":
		config.read(["config/gpstracker.conf"])
	else:
		config.read([os.path.dirname(sys.argv[0]) + "/config/gpstracker.conf"])

	tempfile = config.get("general", "tempfile")
	logfile = config.get("general", "logfile")
	server = config.get("general", "server")
	sitelocation = config.get("general", "sitelocation")
	serverport = int(config.get("general", "serverport"))
	servercert_file = config.get("general", "servercert_file")
	username = config.get("general", "username")
	password = config.get("general", "password")
	submissioninterval = int(config.get("general", "submissioninterval"))
	gpslogginginterval = int(config.get("general", "gpslogginginterval"))

	# parse chosen sync always option and get libc
	if int(config.get("general", "syncalways")) == 0:
		syncalways = False
		libc = None
	else:
		syncalways = True
		libc = ctypes.CDLL("libc.so.6")

	# parse chosen log level
	if config.get("general", "loglevel") == "DEBUG":
		loglevel = logging.DEBUG
	elif config.get("general", "loglevel") == "INFO":
		loglevel = logging.INFO
	elif config.get("general", "loglevel") == "WARNING":
		loglevel = logging.WARNING
	elif config.get("general", "loglevel") == "ERROR":
		loglevel = logging.ERROR
	elif config.get("general", "loglevel") == "CRITICAL":
		loglevel = logging.CRITICAL
	else:
		raise ValueError("No valid log level in config file")
except:
	raise ValueError("Config could not be parsed")


if __name__ == '__main__':

	# initialize logging
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
		datefmt='%m/%d/%Y %H:%M:%S', filename=logfile, level=loglevel)

	# initialize file lock variable
	filelock = threading.Semaphore(1)

	# check temp file exists
	if not os.path.exists(tempfile):
		# create new file if not exists
		try:
			filehandler = open(tempfile, 'wb')
			filehandler.close()
		except:
			logging.error("[%s]: Can not create tempfile under %s" \
				% (__file__, tempfile))
			sys.exit()

	# initialize GPSDataUpdater process and start it
	GPSDataUpdaterProcess = GPSDataUpdater()
	GPSDataUpdaterProcess.start()

	# initialize GPSDataSubmitter process and start it
	GPSDataSubmitterProcess = GPSDataSubmitter(tempfile, filelock, 
		server, serverport, servercert_file, sitelocation, username, 
		password, submissioninterval, syncalways)
	GPSDataSubmitterProcess.start()

	# initialize compare variables
	lastlatitude = 0.0
	lastlongitude = 0.0
	lastaltitude = 0.0

	logging.info("[%s]: Starting with %s sec logging interval..." \
		% (__file__, gpslogginginterval))

	try:
		while 1:
			# wait 5 seconds until checking all processes again
			time.sleep(gpslogginginterval)

			# check GPSDataUpdaterProcess is still alive
			if not GPSDataUpdaterProcess.isAlive():
				logging.error("[%s]: GPSDataUpdater process is" \
					+ " not running ..." % (__file__))

				logging.error("[%s]: Trying to restart GPSDataUpdater " \
					+ "process ... " % (__file__))
					
				# initialize GPSDataUpdater process and start it
				GPSDataUpdaterProcess = GPSDataUpdater()
				GPSDataUpdaterProcess.start()

				# check GPSDataSubmitterProcess is still alive
				if not GPSDataSubmitterProcess.isAlive():
					logging.error("[%s]: GPSDataSubmitter process is not "\
						+ "running ..." % (__file__))

					logging.error("[%s]: Trying to restart " \
						+ "GPSDataSubmitter process ... " % (__file__))

					# initialize GPSDataSubmitter process and start it
					GPSDataSubmitterProcess = GPSDataSubmitter(tempfile, 
						filelock, server, serverport, servercert_file, 
						sitelocation, username, password, submissioninterval)
					GPSDataSubmitterProcess.start()

			# get GPS data
			latitude, longitude, altitude, utctime, speed = \
				GPSDataUpdaterProcess.getValues()

			# python gpsd gives us a string such as 
			# "2014-02-07T16:41:51.500Z" back
			# => convert to timestamp
			if isinstance(utctime, str) or isinstance(utctime, unicode):

				# sometimes the string is empty or not correct
				try:
					tempDate = datetime.datetime.strptime(utctime, 
						'%Y-%m-%dT%H:%M:%S.%fZ')
				except ValueError:
					logging.debug("[%s]: No valid utctime" % (__file__))
					continue

				utctime = 0.0
				utctime = (time.mktime(tempDate.timetuple()) 
					+ (tempDate.microsecond / 1000000.))
			else:
				logging.debug("[%s]: No valid utctime" % (__file__))
				continue

			# check data is valid for processing
			if (latitude == None 
				and longitude == None 
				and altitude == None 
				and speed == None):
				logging.debug("[%s]: No valid gps data" % (__file__))
				continue
			try:
				if (latitude == 0.0 
					or math.isnan(latitude) 
					or longitude == 0.0 
					or math.isnan(longitude) 
					or math.isnan(altitude) 
					or math.isnan(speed)):
					logging.debug("[%s]: No valid gps data" % (__file__))
					continue
			except TypeError:
				logging.debug("[%s]: No valid gps data (TypeError)" \
					% (__file__))
				continue

			# check position has changed (if not continue)
			# altitude differs while standing from 119.2 to 126.9
			# using a tolerance from -9 to 9 for altitude
			# latitude differs while standing from 21.395338333 to 21.395395
			# using a tolerance from -0.00013 to 0.00013
			# longitude differs while standing from 2.211686667 to 2.211846667
			# using a tolerance from -0.0002 to 0.0002
			if (((lastaltitude - altitude) > -9 
				and (lastaltitude - altitude) < 9) 
				and ((lastlatitude - latitude) > -0.00013 
				and (lastlatitude - latitude) < 0.00013) 
				and ((lastlongitude - longitude) > -0.0002 
				and (lastlongitude - longitude) < 0.0002)):
				logging.debug("[%s]: Position has not changed" % (__file__))
				continue

			logging.debug("[%s]: Lock acquire" % (__file__))
			# lock file access
			filelock.acquire()

			# write data in csv format to tempfile
			with open(tempfile, 'ab') as filehandler:
				csvwriter = csv.writer(filehandler, delimiter=';')
				csvwriter.writerow([latitude, longitude, altitude, 
					utctime, speed])
				logging.debug("[%s]: Writing GPS data: %s %s %s %s %s" \
					% (__file__, latitude, longitude, altitude, 
					utctime, speed))

			# check if sync is activated 
			# => sync filesystem to force writing on storage
			if syncalways:
				libc.sync()
			
			# unlock file access
			filelock.release()
			logging.debug("[%s]: Lock released" % (__file__))

			# store position of this round to get changes for the next
			lastlatitude = latitude
			lastlongitude = longitude
			lastaltitude = altitude

	except:
		logging.info("[%s]: Exception: %s" % (__file__, sys.exc_info()))
		pass
	finally:
		# end GPSDataUpdater process
		logging.warning("[%s]: Exiting GPSDataUpdater process ..." \
			% (__file__))
		GPSDataUpdaterProcess.exit()

		# end GPSDataSubmitter process
		logging.warning("[%s]: Exiting GPSDataSubmitter process ..." \
			% (__file__))
		GPSDataSubmitterProcess.exit()
