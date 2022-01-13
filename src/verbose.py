#!/usr/bin/python

# shared/verbose.py
#
# Mike Bonnington <mjbonnington@gmail.com>
# (c) 2013-2021
#
# This module handles the output of messages, warnings and errors.


import logging
import os
import re
#import sys

try:
	from plyer import notification
	notifications = True
except (ImportError, TypeError):
	print("Missing dependency: Plyer\n  Unable to show desktop notifications.")
	notifications = False


global statusBar
global activityLog
global _inline_message_flag

statusBar = None
activityLog = None
_inline_message_flag = False

# Enable VT100 escape sequence for Windows 10 ver. 1607
if os.getenv('IC_ENV') == 'standalone':
	os.system('')

# Define some ANSI colour codes
class bcolors:
	if os.getenv('IC_ENV') == 'standalone':
		HEADER = '\033[95m'
		OKBLUE = '\033[38;5;081m' #'\033[94m'
		OKGREEN = '\033[92m'
		WARNING = '\033[38;5;186m' #'\033[93m'
		FAIL = '\033[38;5;197m' #'\033[91m'
		ENDC = '\033[0m'
		BOLD = '\033[1m'
		UNDERLINE = '\033[4m'
		BRIGHT = '\033[38;5;015m'
		DARK = '\033[38;5;241m'
		INVERT = '\033[7m'
		INLINE = u'\u001b[1A\u001b[1000D\u001b[0K'
	else:
		HEADER = ''
		OKBLUE = ''
		OKGREEN = ''
		WARNING = ''
		FAIL = ''
		ENDC = ''
		BOLD = ''
		UNDERLINE = ''
		BRIGHT = ''
		DARK = ''
		INVERT = ''
		INLINE = ''


def registerStatusBar(statusBarObj):
	""" Register a QStatusBar object with this module so that messages can be
		printed to the appropriate UI status bar.
		Note: call this function with the argument None (to de-register global
		statusBar) before running any functions from this module in a thread.
	"""
	global statusBar
	statusBar = statusBarObj


def setup_logger(name, log_file, level=logging.INFO):
	""" Function to create and setup multiple loggers.
	"""
	global activityLog

	formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")

	handler = logging.FileHandler(log_file)
	handler.setFormatter(formatter)

	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.addHandler(handler)

	#return logger
	activityLog = logger


def notify_(**kwargs):
	""" Display a desktop notification message using plyer.
	"""
	if notifications:
		kwargs['timeout'] = int(os.getenv('IC_NOTIFICATIONS_TIMEOUT', 5))
		notification.notify(**kwargs)
	else:
		message(kwargs['message'])


def debug(message, log=False):
	""" Print a debugging message.
	"""
	global activityLog

	print_("DEBUG: " + message, 5)
	if log and activityLog:
		activityLog.debug(message)

def detail(message, log=False):
	""" Print a detailed info message.
	"""
	global activityLog

	print_(message, 4)
	if log and activityLog:
		activityLog.info(message)

def message(message, log=False, notify=False):
	""" Print an info message.
	"""
	global activityLog

	print_(message, 3)
	if log and activityLog:
		activityLog.info(message)

	if notify and notifications:
		notify_(title=os.getenv('IC_NAME'), message=message, app_name=os.getenv('IC_NAME'), app_icon=os.getenv('IC_APPICON'), timeout=2)


def progress(message, log=False):
	""" Print a progress message.
	"""
	global activityLog

	print_(message, 3, inline=True)
	if log and activityLog:
		activityLog.info(message)

def warning(message, log=False):
	""" Print a warning message.
	"""
	global activityLog

	print_("Warning: " + message, 2)
	if log and activityLog:
		activityLog.warning(message)

def error(message, log=False):
	""" Print an error message.
	"""
	global activityLog

	print_("ERROR: " + message, 1)
	if log and activityLog:
		activityLog.error(message)


def print_(message, verbosityLevel=4, status=True, inline=False, log=False):
	""" Print the message to the console.
		If 'status' is True, the message will be shown on the main UI status
		bar.
		If 'inline' is True, the message will overwrite the previous line
		where allowed.
		If 'log' is True, the message will be written to a logfile (not yet
		implemented).

		Verbosity levels:
		0 - Nothing is output
		1 - Errors and messages requiring user action
		2 - Errors and warning messages
		3 - Info and progress messages (default)
		4 - Detailed info messages
		5 - Debugging messages
	"""
	# Avoid errors if the type of 'message' is not a string by bypassing the
	# rest of this function and passing the message directly to the builtin
	# print function...
	try:  # Python 2.x
		if type(message) not in [str, unicode]:
			print(message)
			return
	except NameError:  # Python 3.x
		if type(message) is not str:
			print(message)
			return

	global statusBar
	global activityLog
	global _inline_message_flag

	verbositySetting = int(os.getenv('IC_VERBOSITY', 3))

	# Print message to the status bar
	if verbosityLevel <= 3 and status and statusBar is not None:
		timeout = 1800 + max(2400, len(message)*60)
		statusBar.showMessage(message, timeout)

	# Print message to the console
	if verbosityLevel <= verbositySetting:
		# Add ANSI color codes
		if os.getenv('IC_ENV') == 'standalone':
			if verbosityLevel == 5:
				message = bcolors.DARK + bcolors.INVERT + message + bcolors.ENDC
			elif verbosityLevel == 4:
				message = bcolors.DARK + message + bcolors.ENDC
			elif verbosityLevel == 3:
				message = bcolors.OKBLUE + message + bcolors.ENDC
			elif verbosityLevel == 2:
				message = bcolors.WARNING + message + bcolors.ENDC
			elif verbosityLevel == 1:
				message = bcolors.FAIL + message + bcolors.ENDC

		# Print inline
		if inline:
			# sys.stdout.write(u"\u001b[1000D" + message)
			# sys.stdout.flush()
			if _inline_message_flag and verbosityLevel < 5:
				print(bcolors.INLINE + message)
			else:
				print(message)
			_inline_message_flag = True
		else:
			print(message)
			_inline_message_flag = False


def pluralise(noun, count=0):
	""" Pluralise nouns.
		if 'count' variable is given, return singular if count is 1, otherwise
		return plural form.
		In the name of simplicity, this function is far from exhaustive.
	"""
	if count == 1:
		return noun

	if re.search('[^fhms][ei]x$', noun):
		return re.sub('[ei]x$', 'ices', noun)
	elif re.search('[sxz]$', noun):
		return re.sub('$', 'es', noun)
	elif re.search('[^aeioudgkprt]h$', noun):
		return re.sub('$', 'es', noun)
	elif re.search('[^aeiou]y$', noun):
		return re.sub('y$', 'ies', noun)
	elif re.search('ies$', noun):
		return noun
	else:
		return noun + 's'


# Specific messages follow in alphabetical order.
# Note - Unless the message is generic and frequently re-used, it is
# preferable to keep the message text within the outputting module, using the
# progress(), message(), warning() and error() methods of this module.

# ...

# # Print launch initialisation message
# print_("\n%s%s%s %s" % (bcolors.INVERT, os.getenv('IC_NAME'), bcolors.ENDC, os.getenv('IC_VERSION')), 0)
# print_("%s %s" % (os.getenv('IC_COPYRIGHT'), os.getenv('IC_VENDOR')), 0)
# print_('', 0)  # add newline
