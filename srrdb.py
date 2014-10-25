#!/usr/bin/env python
# -*- coding: latin-1 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

"""
How it works:
-------------

!! Beware of side effects. Use the -n parameter before uploading. !!

This script allows you to upload new SRR files to srrdb.com:
   srrdb.py first.file.srr second.release.srr
   srrdb.py ./dir/structure/with/srr/files
   
It also allows you to _batch_ upload additional files such as .srs files:
   srrdb.py /path/to/a/directory/ C:\or\Windows\style
   srrdb.py . -n
   srrdb.py . -e .avi.txt,.mkv.txt --fix-txt -n
Each directory must be structured in the following way:
   +---Release-Name/
   |       file.to.store.srs
   |
   +---Other.Release-Name/
   |   |
   |   +---Sample/
   |       unreconstructable.sample.avi.txt
   |...
It will walk the tree and tries to detect the release name based on bad
directory names. SRS files are automatically put in a Sample/ folder. 
Other files do not get a folder set.
Vobsub .srr files aren't supported yet with this method?
See _SUPPORTED_FILES for the type of files that are detected for upload.

Download Python 2.7 from http://www.activestate.com/activepython/downloads
http://www.blog.pythonlibrary.org/2011/11/24/python-101-setting-up-python-on-windows/

Install the dependencies that are necessary for this script:
  pypm.exe install poster
or if you use the regular CPython version:
  easy_install.exe poster
http://pypi.python.org/pypi/setuptools

Version history:
0.1 (2011-10-17) http://www.mediafire.com/file/9bidbasgtg2nggr/srrdb_0.1.zip
	- Initial release available for public usage
0.2 (2011-11-24) http://www.mediafire.com/file/d5y4tfyha53lwfd/srrdb_0.2.zip
	- recursively adds files (when srs is in Sample directory)
	- clean up .txt files
0.3 (2012-10-18) http://www.mediafire.com/file/hvvtpzo0pkn0vj6/srrdb_0.3.zip
	- keeps sample directory capitalization
	- crashed on gme-comandante_2003)_sample.srs
0.4 (2012-10-28)
	- txt fixing improved
0.5 (2013-01-06)
	- fixed for v2 of the site
	- rellist code removed
0.6 (2013-06-23)
	- fixed for v2.5 of the site
0.7 (2014-10-25)
	- max file size updated to 52428800
	- fix for encoding issue on Russian Windows
	- continue uploading when errors occur

Author: Gfy <clerfprar@tznvy.pbz>
"""

from __future__ import unicode_literals
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from urllib2 import HTTPCookieProcessor, ProxyHandler, Request
import urllib
import urllib2
import httplib
import cookielib
import re
import os
import optparse
import sys
import time
import ConfigParser
import codecs

# supported extensions for files to add to a release
# checks config file and -e parameter later on
_SUPPORTED_FILES = (".srs", ".srr",
                    ".avi.txt", ".mkv.txt", ".mp4.txt", ".wmv.txt",
                    ".vob.txt", ".m2ts.txt", 
                    ".mpg.txt", ".mpeg.txt", ".m2v.txt", ".m4v.txt") 

__version__ = "0.7"
_USER_AGENT = "Gfy's srrDB upload script version %s." % __version__

# some configuration options
_PROXY = False
_PROXY_TYPE = "http"
_PROXY_URL = "http://127.0.0.1:8008" # WebScarab

# srrdb.com credentials
_USERNAME = ""
_PASSWORD = ""
_URL = "http://www.srrdb.com/"

def fix_txt(file_path):
	""" Cleans up .ext.txt files created by the DOS script. """
	if options.dry_run:
		print("Fixing '%s'." % os.path.basename(file_path))
		return
	data = codecs.open(file_path, encoding="latin-1", mode="r").read()
	newdata = re.sub(".*Corruption ", "Corruption ", data)
	newdata = re.sub(".*Unexpected Error", "Unexpected Error", newdata)
	newdata = newdata.replace("\xff", ".") # cp850 \xa0
	newdata = newdata.replace("\xa0", ".")
	newdata = re.sub("\r(?!\n)|(?<!\r)\n", "\r\n", newdata)
	if newdata != data:
		print("'%s' fixed." % os.path.basename(file_path))
		f = open(file_path, "wb")
		f.write(newdata.encode('latin-1'))
		f.close()
	else:
		print("Nothing done for %s!" % os.path.basename(file_path))

class urlErrorDecorator(object):
	""" Decorator to share the same error handling code for the url calling
	stuff needed by a lot of functions.
	A nice intro to decorators:
	http://www.artima.com/weblogs/viewpost.jsp?thread=240808 
	http://wiki.python.org/moin/PythonDecoratorLibrary """
	def __init__(self, f):
		self.f = f
		self.attempt = 0

	def __call__(self, *args, **kwargs):
		# http://stackoverflow.com/questions/3465704/
		# python-urllib2-urlerror-http-status-code
		try:
			self.attempt += 1
			return self.f(*args, **kwargs)
		except urllib2.HTTPError as e:
			print("!!!! We failed with error code - %s." % e.code)
			if self.attempt <= 5:
				sleeptime = 5.0 * self.attempt
				print("Retrying again after %d seconds..." % sleeptime)
				time.sleep(sleeptime)
				return self.__call__(*args, **kwargs)
		except urllib2.URLError as e:
			print("This usually means the server doesn't exist, is down, "
				  "or you don't have an Internet connection.")
			print("!!!! The error object has the following 'args' attribute:")
			print(e.args)
		except httplib.HTTPException: 
			# IncompleteRead(271 bytes read, 606 more expected)
			# duplicate uploads could cause larger file queues?
			#     -> only when rarhash doesn't match
			# httplib.BadStatusLine: ''
			if self.attempt <= 5:
				sleeptime = 5.0 * self.attempt
				print("Retrying again after %d seconds..." % sleeptime)
				time.sleep(sleeptime)
				return self.__call__(*args, **kwargs)
		except ValueError as e:
			print("The URL is invalid or blank. Terminating.")
			sys.exit(1)

class Srrdb(object):
	""" Class that supports stuff from srrdb.com """
	def __init__(self, username, password):
		self.cj = cj = cookielib.CookieJar()
		
		# set up proxy to check sent requests with WebScarab
		if _PROXY:
			proxy_support = ProxyHandler({_PROXY_TYPE : _PROXY_URL})
			self.opener = urllib2.build_opener(proxy_support, 
								HTTPCookieProcessor(cj))
		else:
			self.opener = urllib2.build_opener(HTTPCookieProcessor(cj))
		urllib2.install_opener(self.opener)
		
		self.baseurl = _URL
		self.username = username
		self.body = {
				'username' : username,
				'password' : password,
				'login': 'Login'
				}
		self.headers = { 
				'Referer' : self.baseurl,
				'User-Agent' : _USER_AGENT,
				}
		self._login(self)

	@urlErrorDecorator
	def _login(self):
		""" Authenticate. """  
		data = urllib.urlencode(self.body)
		request = urllib2.Request(self.baseurl + "account/login", 
		                          data, self.headers)
		html_source = self.opener.open(request).read()
		res = re.findall("%s<br />" % self.username, html_source)
		if len(res):
			print("Authentication successful.")
			matches = re.findall(".*logged-in-links.*/account/profile/(\d+).*",
								html_source)
			self.user_id = matches[0]
			print("%s has user id %s." % (self.username, self.user_id))
		else:
			print("Authentication unsuccessful.") # or the site has changed

	@urlErrorDecorator
	def add_file(self, release, filename, folder):
		""" release: the release name
		filename: path where to find the file on HD
		folder: the folder to the SRR e.g. "Sample" without the /
		"""
		# http://stackoverflow.com/questions/680305/
		# using-multipartposthandler-to-post-form-data-with-python
		# Register the streaming http handlers with urllib2
		opener = register_openers()
		# https://bitbucket.org/chrisatlee/poster/issue/7/
		# multipart-form-post-doesnt-work-with
		if _PROXY:
			opener.add_handler(ProxyHandler({_PROXY_TYPE : _PROXY_URL}))
						
		# Start the multipart/form-data encoding of the file "DSC0001.jpg"
		# "image1" is the name of the parameter, which is normally set
		# via the "name" parameter of the HTML <input> tag.
		
		# Ensure file is Unicode:
		filename = filename.decode(sys.getfilesystemencoding())
		
		# new_headers contains the necessary Content-Type and Content-Length
		# datagen is a generator object that yields the encoded parameters
		datagen, new_headers = multipart_encode({
				"folder" : folder,
				"MAX_FILE_SIZE" : 52428800,
				"file": open(filename, "rb"),
				"add": "Add",})
		headers = dict(self.headers) # makes copy original dict
		headers.update(new_headers)
		url = self.baseurl + "release/add/" + release
		request = Request(url, datagen, headers)
		opener.add_handler(HTTPCookieProcessor(self.cj))
		
		if folder != "":
			fn = folder + "/"
		else:
			fn = ""
		fn += os.path.basename(filename)

		# Actually do the request, and get the response
		try:
			handle = urllib2.urlopen(request)
			html_source = handle.read()
			
			# sre_constants.error: unbalanced parenthesis
			if len(re.findall(".*%s.*" % re.escape(fn), html_source)):
				print("'%s' successfully uploaded." % fn)
				# also gives this result if it was already there in the first place
				success = True
	#		elif len(re.findall(".*an error occurred while adding the file.*", 
	#							html_source)):  
	#			print("!!! '%s': file already added." % fn)
	#			success = False
			else:
				print(html_source)
				print("The site has been changed.")
				success = False
		except urllib2.HTTPError as e:
			if e.code == 404:
				print("!!! '%s': no such release." % release)
				success = False
			else:
				raise
		
		return success

	@urlErrorDecorator
	def add_release(self, srr_file):
		""" srr_file: the srr file to upload  """
		opener = register_openers()
		if _PROXY:
			opener.add_handler(ProxyHandler({_PROXY_TYPE : _PROXY_URL}))

		# Ensure file is Unicode:
		srr_file = srr_file.decode(sys.getfilesystemencoding())
		datagen, new_headers = multipart_encode({
				"MAX_FILE_SIZE" : 52428800,
				"file": open(srr_file, "rb"),
				"upload": "Upload",})
		headers = dict(self.headers) # makes copy original dict
		headers.update(new_headers)
		
		url = self.baseurl + "upload"
		request = Request(url, datagen, headers)
		opener.add_handler(HTTPCookieProcessor(self.cj))

		# Actually do the request, and get the response
		handle = urllib2.urlopen(request)
		html_source = handle.read()
		
		if len(re.findall(".* was uploaded\.", html_source)):
			print("'%s' was added." % srr_file)
			return True
		elif len(re.findall(".* is.*administrator.*", html_source)):
			print("!!! '%s' already exists." % srr_file)
		elif len(re.findall(".*contains illegal characters.*", html_source)):
			print("!!! '%s' contains illegal characters." % srr_file)
		else:
			print(html_source)
		return False
	
def read_config():
	"""The configuration file is in the same directory as the application."""
	folder = os.path.dirname(os.path.realpath(sys.argv[0]))
	config = ConfigParser.ConfigParser()
	global _SUPPORTED_FILES, _USERNAME, _PASSWORD, _URL,  \
			_PROXY, _PROXY_TYPE, _PROXY_URL
	cfile = os.path.join(folder, 'srrdb.cfg')
	try:
		with open(cfile, 'r') as config_file:
			config.readfp(config_file)
		_USERNAME = config.get("login", "username")
		_PASSWORD = config.get("login", "password")
		_URL = config.get("site", "url")
		_SUPPORTED_FILES = config.get("extensions", "ext").split(",")
		if config.getboolean("site", "proxy_enabled"):
			_PROXY = True
			_PROXY_TYPE = config.get("site", "proxy_type")
			_PROXY_URL = config.get("site", "proxy_url")
	except IOError as e:
		# create config file
		config.add_section("login")
		config.set("login", "username", "username")
		config.set("login", "password", "password")
		
		config.add_section("site")
		config.set("site", "url", _URL)
		config.set("site", "proxy_type", _PROXY_TYPE)
		config.set("site", "proxy_url", _PROXY_URL)
		config.set("site", "proxy_enabled", _PROXY)
		
		config.add_section("extensions")
		config.set("extensions", "ext", ",".join(_SUPPORTED_FILES))
		
		config.write(open(cfile, 'w'))
	except ConfigParser.NoOptionError as e:
		print(e)

def guess_releasename(path):
	# Mr.Vampire.1985.PROPER.DVDRip.XviD-SAPHiRE - 'Samples' folder
	(head, tail) = os.path.split(path)
	if re.match("^(vob)?(samples?|subs?|proofs?|covers?)$|(.*nfofix.*)",
		        tail, re.IGNORECASE):
		return guess_releasename(head)
	else:
		return tail
		
def process_file(srrdb, path, pfile):
	""" returns (processed, success) """
	lengths = set([len(f) for f in _SUPPORTED_FILES])
	# the file has one of the allowed extentions
	if len(filter(lambda l: pfile[-l:] in _SUPPORTED_FILES, lengths)):
		relname = guess_releasename(path)
		srr_dir = ""
		if pfile[-4:] in (".srs", ".txt"):
			srr_dir = "Sample"
			# sometimes the dirs can be 'sample' or 'SAMPLE' too
			# try to keep original dir naming if possible
			(_head, tail) = os.path.split(path)			  
			if tail.lower() == "sample":
				srr_dir = tail
		if pfile[-4:] in (".jpg", ".png", ".gif", ".bmp"):
			(_head, tail) = os.path.split(path)			  
			if tail.lower() == "proof":
				srr_dir = tail
			else:
				srr_dir = ""
#				return (False, False)
		if pfile[-4:] in (".sfv"):
			(_head, tail) = os.path.split(path)			  
			if "sub" in tail.lower():
				srr_dir = tail
			else:
				srr_dir = ""

		# nfofix dir is not detected as being a release dir
		if ".nfo" in pfile:
			(_head, tail) = os.path.split(path)
			if "nfofix" in tail.lower():
				srr_dir = tail
				
		print("Storing file '%s' in '%s' with release" % (pfile, srr_dir))
		print("             '%s'." % relname)
		if not options.dry_run:
			os.chdir(path)
			pause_exec()
			if not srrdb.add_file(srrdb, relname, pfile, srr_dir):
				return (True, False)
		return (True, True)
	return (False, False)
	
def pause_exec():
	time.sleep(options.sleeptime)
		
def main(options, args):
	read_config()
	
	# overwrite config if an other parameter is given
	global _SUPPORTED_FILES, _USERNAME, _PASSWORD
	if options.extensions:
		_SUPPORTED_FILES = options.extensions.split(',')
	if options.login:
		_USERNAME = options.login
	if options.password:
		_PASSWORD = options.password
		
	print("Site: %s" % _URL)
	if _PROXY:
		print("Proxy: %s" % _PROXY_URL)
	
	if not options.dry_run:
		try:
			s = Srrdb(_USERNAME, _PASSWORD)
		except:
			print("Uploading files files as anonymous.")
			print("Show me this:")
			print(sys.exc_info())
	else:
		print("Script running as a dry run: no site lookups are done.")
		s = None

	add_count = srr_count = add_error = srr_dupe = 0
	for element in args:
		element = os.path.abspath(element)
		dirname = os.path.dirname(element)
		basename = os.path.basename(element)
		if os.path.isfile(element) and element[-4:] == ".srr":
			srr_count += 1
			if options.dry_run:
				print("Uploading '%s'." % element)
			else:
				# change current working dir 
				# (so no path info is send to the server
				os.chdir(dirname)
				pause_exec()
				if not s.add_release(s, basename):
					srr_dupe += 1
				sys.stdout.flush()
		elif os.path.isdir(element):
			print("Processing files to upload (%s)" % element)
			# add srs, jpg, jpeg, png files to the actual release on site
			# only walk folders and add these files
			for dirpath, _dirnames, filenames in os.walk(element):
				for fname in filenames:
					# just fix .txt files; will overwrite the text fname
					if fname[-4:] == ".txt" and options.fix_txt:
						try:
							fix_txt(os.path.join(dirpath, fname))
						except:
							print("Fixing failed for %s. Quitting." % fname)
							print(sys.exc_info())
							sys.exit(1)
					# add a new release (.srr) to the database
					# TODO: should be adding .srr in the release (for subs)
					# if it contains vobsubs
					if fname[-4:] == ".srr" and fname[-4:] in _SUPPORTED_FILES:
						srr_count += 1
						if options.dry_run:
							print("Uploading '%s'." % fname)
						else:
							os.chdir(dirpath)
							pause_exec()
							if not s.add_release(s, fname):
								srr_dupe += 1
							sys.stdout.flush()
					# store files in the SRR on the site
					else:
						(processed, success) = process_file(s, dirpath, fname)
						if processed:
							add_count += 1
							if not success:
								add_error += 1
						sys.stdout.flush()
		else:
			print("WTF are you supplying me?")
	
	plural = lambda amount: "s" if amount != 1 else ""
	if srr_count:
		print("%d new SRR file%s uploaded. %d error%s." % 
			(srr_count, plural(srr_count), srr_dupe, plural(srr_dupe)))
	if add_count:
		print("%d file%s processed. %d problem%s." % 
			(add_count, plural(add_count), add_error, plural(add_error)))

if __name__ == '__main__':
	parser = optparse.OptionParser(
		usage="Usage: %prog [SRR file(s)] [directories] [options]'\n"
		"This tool will upload new SRR files or store additional files "
		"such as samples on srrdb.com.\n",
		version="%prog " + __version__) # --help, --version
	
	auth = optparse.OptionGroup(parser, "Authentication")
	auth.set_description("The credentials that are needed to login to "
						 "srrdb.com. SRR files will but uploaded anonymously "
						 "if no or no correct credentials are supplied.")
	parser.add_option_group(auth)
	
	auth.add_option("-l", "--login", help="supply username", 
					 metavar="USERNAME", default=_USERNAME, dest="login")
	auth.add_option("-p", "--password", help="supply password", 
					 metavar="PASSWORD", default=_PASSWORD, dest="password")
	
	parser.add_option("-n", "--dry-run", help="do no harm but will fix "
					  "txt files when -t is used",
					  action="store_true", dest="dry_run", default=False)
	parser.add_option("-e", "--extensions", 
					  help="only add files with one of these extensions "
					  "to a release",
					  action="store", dest="extensions")
	parser.add_option("-t", "--fix-txt", help="fixes .txt files",
					  action="store_true", dest="fix_txt", default=False)
	parser.add_option("--sleeptime", help="seconds to sleep (float)",
					  type="float", dest="sleeptime", default=0.0) 
	
	# no arguments given
	if len(sys.argv) < 2:
		print(parser.format_help())
	else:	   
		(options, args) = parser.parse_args()
		main(options, args)
	