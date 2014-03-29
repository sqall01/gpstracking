#!/usr/bin/python

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org)
# 
# Licensed under the GNU Public License, version 2.

import threading
import csv
import sys
import time
import os
import httplib
import urllib
import base64
import logging
# for VerifiedHTTPSConnection class
import socket
import ssl
import ctypes

# HTTPSConnection like class that verify server certificates
class VerifiedHTTPSConnection(httplib.HTTPSConnection):
	# needs socket and ssl lib
	def __init__(self, host, port=None, servercert_file=None, 
		key_file=None, cert_file=None, strict=None, 
		timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
		httplib.HTTPSConnection.__init__(self, host, port, key_file, 
			cert_file, strict, timeout)
		self.servercert_file = servercert_file

	# overrides the original version in httplib of python 2.6
	def connect(self):
		"Connect to a host on a given (SSL) port."

		sock = socket.create_connection((self.host, self.port), self.timeout)
		if self._tunnel_host:
			self.sock = sock
			self._tunnel()

		# the only thing to change in the original connect function from
		# httplib (tell ssl.wrap_socket to verify server certificate)
		self.sock = ssl.wrap_socket(sock, self.key_file, 
			self.cert_file, cert_reqs=ssl.CERT_REQUIRED, 
			ca_certs=self.servercert_file)


class GPSDataSubmitter(threading.Thread):
	def __init__(self, tempfile, filelock, server, serverport, 
		servercert_file, sitelocation, username, password, 
		submissioninterval, syncalways):
		logging.debug("[%s]: Initializing GPSDataSubmitter" % (__file__))

		threading.Thread.__init__(self)

		self.exitflag = False
		self.tempfile = tempfile
		self.filelock = filelock
		self.server = server
		self.serverport = serverport
		self.sitelocation = sitelocation
		self.submissioninterval = submissioninterval
		self.servercert_file = servercert_file
		self.syncalways = syncalways

		# if sync option is activated => get libc
		if self.syncalways:
			self.libc = ctypes.CDLL("libc.so.6")
		else:
			self.libc = None

		# initialize headers for HTTP request
		self.headers = {"Connection": "keep-alive", 
			"Content-type": "application/x-www-form-urlencoded", 
			"Accept": "text/plain", 
			"Authorization": "Basic " 
			+ base64.b64encode(username + ":" + password)}

		# set thread to daemon
		threading.daemon = True

	def run(self):
		logging.info("[%s]: Starting GPSDataSubmitter with %s sec interval" \
			% (__file__, self.submissioninterval))
		while 1:
			# wait submissioninterval rounds one second 
			# and check every round exit flag
			for i in range(self.submissioninterval):
				time.sleep(1)

				# check exit flag and if set => exit
				if self.exitflag:
					logging.debug("[%s]: Quitting GPSDataSubmitter" \
						% (__file__))
					return

			# check file size and if empty continue
			if os.path.getsize(self.tempfile) == 0:
				continue

			# initialize HTTP object for connection
			#conn = httplib.HTTPSConnection(self.server, self.serverport)
			conn = VerifiedHTTPSConnection(self.server, self.serverport, 
				self.servercert_file)

			# extract data and send to server
			csvdata = ""

			# lock file access
			logging.debug("[%s]: Lock acquire" % (__file__))				
			self.filelock.acquire()

			# check for unprocessed GPS data
			try:				
				if os.path.getsize(self.tempfile + "_processing") > 0:
					logging.info("[%s]: Unclean shutdown detected." \
						+ " Recovering data ..." % (__file__))

					# get all unprocessed GPS data from file
					with open(self.tempfile + "_processing", 'rb') \
						as processinghandler:
						recoveringdata = processinghandler.read()

					# add unprocessed data to normal GPS data file
					with open(self.tempfile, 'ab') as filehandler:
						filehandler.write(recoveringdata)

					# check if sync is activated 
					# => sync filesystem to force writing on storage
					if self.syncalways:
						self.libc.sync()

					# clear unprocessed data file
					with open(self.tempfile + "_processing", 'wb') \
						as filehandler:
						pass					

					logging.info("[%s]: Recovering completed" % (__file__))
			except:
				pass


			# open file for reading
			with open(self.tempfile, 'rb') as filehandler:
				# get all data from file
				csvdata = filehandler.readlines()

				# make copy of data that is processed
				with open(self.tempfile + "_processing", 'wb') \
					as processinghandler:
					processinghandler.write("".join(csvdata))

			# clear csv file
			with open(self.tempfile, 'wb') as filehandler:
				pass

			# unlock file access
			self.filelock.release()
			logging.debug("[%s]: Lock released" % (__file__))

			# submit all GPS data
			for dataset in csvdata:

				# strip and split dataset (which is a string)
				dataset = dataset.strip().split(";")

				# remove 0x00 bytes 
				# (sometimes in files because of powerfail of client)
				latitude = dataset[0].replace("\x00", "")
				longitude = dataset[1].replace("\x00", "")
				altitude = dataset[2].replace("\x00", "")
				utctime = dataset[3].replace("\x00", "")
				speed = dataset[4].replace("\x00", "")

				# urlencode the data
				params = urllib.urlencode({'latitude': latitude, 
					'longitude': longitude, 
					'altitude': altitude, 
					'utctime': utctime, 
					'speed': speed})

				# try to send POST request with data to server
				try:
					conn.request("POST", self.sitelocation, params, 
						self.headers)
				except ssl.SSLError:
					logging.error("[%s]: SSL server certificate not valid" \
						% (__file__))

					logging.debug("[%s]: Lock acquire" % (__file__)) 
					# lock file access
					self.filelock.acquire()

					# when not successfull write unprocessed data back
					with open(self.tempfile, 'ab') as filehandler:
						filehandler.write("".join(csvdata))

					# check if sync is activated 
					# => sync filesystem to force writing on storage
					if self.syncalways:
						self.libc.sync()

					# clear unprocessed data file
					with open(self.tempfile + "_processing", 'wb') \
						as filehandler:
						pass						

					# unlock file access
					self.filelock.release()
					logging.debug("[%s]: Lock released" % (__file__))

					break
				except:
					logging.warning("[%s]: Server not reachable" % (__file__))

					logging.debug("[%s]: Lock acquire" % (__file__)) 
					# lock file access
					self.filelock.acquire()

					# when not successfull write unprocessed data back
					with open(self.tempfile, 'ab') as filehandler:
						filehandler.write("".join(csvdata))

					# check if sync is activated 
					# => sync filesystem to force writing on storage
					if self.syncalways:
						self.libc.sync()

					# clear unprocessed data file
					with open(self.tempfile + "_processing", 'wb') \
						as filehandler:
						pass

					# unlock file access
					self.filelock.release()
					logging.debug("[%s]: Lock released" % (__file__))

					break	
				response = conn.getresponse()

				# check response is not successfull
				if response.status != 200:
					logging.warning("[%s]: Sending request to server " +
						"failed: %s %s" % (__file__, response.status, 
						response.reason))

					logging.debug("[%s]: Lock acquire" % (__file__))
					# lock file access
					self.filelock.acquire()

					# when not successfull write unprocessed data back
					with open(self.tempfile, 'ab') as filehandler:
						filehandler.write("".join(csvdata))

					# check if sync is activated 
					# => sync filesystem to force writing on storage
					if self.syncalways:
						self.libc.sync()

					# clear unprocessed data file
					with open(self.tempfile + "_processing", 'wb') \
						as filehandler:
						pass

					# unlock file access
					self.filelock.release()
					logging.debug("[%s]: Lock released" % (__file__))

					break

				response_data = response.read()
					
				# check server accepted the data without error => continue
				if response_data == "ok":
					logging.debug("[%s]: Response: ok" % (__file__))
					continue
				# check server responed with duplicate entry => continue
				elif response_data == "duplicate entries":
					logging.debug("[%s]: Response: duplicate entries" \
						% (__file__))
					continue
				elif response_data == "error data missing":
					logging.debug("[%s]: Response: error data missing" \
						% (__file__))
					continue
				else:
					logging.debug("[%s]: Lock acquire" % (__file__))
					# lock file access
					self.filelock.acquire()

					# when not successfull write unprocessed data back
					with open(self.tempfile, 'ab') as filehandler:
						filehandler.write("".join(csvdata))

					# check if sync is activated 
					# => sync filesystem to force writing on storage
					if self.syncalways:
						self.libc.sync()

					# clear unprocessed data file
					with open(self.tempfile + "_processing", 'wb') \
						as filehandler:
						pass

					# unlock file access
					self.filelock.release()
					logging.debug("[%s]: Lock released" % (__file__))

					logging.debug("[%s]: Response: %s" \
						% (__file__, response_data))

			# clear unprocessed data file
			with open(self.tempfile + "_processing", 'wb') as filehandler:
				pass

			# close connection
			conn.close()

	# sets the exit flag
	def exit(self):
		logging.debug("[%s]: Tell GPSDataSubmitter to quit" % (__file__))
		self.exitflag = True
		return
