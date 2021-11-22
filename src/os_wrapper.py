#!/usr/bin/python

# shared/os_wrapper.py
#
# Mike Bonnington <mjbonnington@gmail.com>
# (c) 2013-2021
#
# This module acts as an OS-independent wrapper for low-level system
# operations.


import json
import os
import re
import shutil
import subprocess
import sys
import traceback

# Import custom modules
import verbose


# Prevent spawned processes from opening a shell window on Windows
CREATE_NO_WINDOW = 0x08000000


def execute(args):
	"""Wrapper to execute a command using subprocess.check_output()."""

	# verbose.detail(" ".join(arg for arg in args))
	verbose.detail(str(args))

	try:
		if os.environ['IC_OS'] == "win":
			output = subprocess.check_output(args, creationflags=CREATE_NO_WINDOW)
		else:
			output = subprocess.check_output(args)
		return True, output.decode()

	# Python 2 errors when decoding output
	except UnicodeDecodeError:
		return True, output.decode('utf-8')

	except subprocess.CalledProcessError as e:
		error_msg = e.output.decode()
		# verbose.error(error_msg)
		# raise RuntimeError(error_msg)
		return False, error_msg


def popen(args):
	"""Wrapper to execute a command using subprocess.Popen()."""

	# verbose.detail(str(args))
	# subprocess.Popen(args, shell=True)

	# Join args list into string
	argstr = " ".join(args)
	verbose.detail(argstr)
	subprocess.Popen(argstr, shell=True)


def call(args):
	"""Wrapper to execute a command using subprocess.call()."""

	# verbose.detail(" ".join(arg for arg in args))
	verbose.detail(str(args))

	subprocess.call(args, shell=True)


def shell():
	"""Open a subshell using the OS default shell in the current environment.
	"""
	if os.environ['IC_OS'] == "win":
		subprocess.Popen(os.environ['IC_SHELL'], shell=True)
	else:
		os.system(os.environ['IC_SHELL'])


def open_(path):
	"""Open the OS native file explorer at the specified directory.

	Can also be used to open any file using its native handler.
	If path is a URL, open in web browser.
	TODO: Translate paths for OS
	"""
	verbose.detail('open "%s"' % path)

	# path = os.path.normpath(path)
	path = translate_path(path)

	try:
		if os.environ['IC_OS'] == "win":
			if path.startswith("//"):  # Fix for UNC paths
				# path = path.replace("/", "\\")
				path = os.path.normpath(path)
			os.startfile(path)
		elif os.environ['IC_OS'] == "mac":
			subprocess.Popen('open %s' % path, shell=True)
		else:
			# subprocess.Popen('gio open %s' % path, shell=True)
			subprocess.Popen('xdg-open %s' % path, shell=True)

		return True

	# except FileNotFoundError as e:  # Not in Python 2.x
	except EnvironmentError as e:
		verbose.error(str(e))
		# verbose.error("Directory not found: %s" % path)
		return False


def mkdir(path):
	"""Create a directory at the specified path."""

	# path = os.path.normpath(path)
	path = translate_path(path)

	if os.path.isdir(path):
		verbose.detail("Directory already exists: %s" % path)
		return path

	else:
		try:
			os.makedirs(path)

			# Hide the folder if its name starts with a dot, as these files
			# are not automatically hidden on Windows
			if os.environ['IC_OS'] == "win":
				if os.path.basename(path).startswith('.'):
					set_hidden(path)

			verbose.detail('mkdir "%s"' % path)  # This causes an error if user config dir doesn't exist
			return path

		except:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			msg = traceback.format_exception_only(exc_type, exc_value)[0]
			verbose.error(msg)
			verbose.error("Cannot create directory: %s" % path)
			return False


def hardlink(source, destination, verify=True):
	"""Create a hard link.

	TODO: rewrite to use os.link()
	"""
	# src = os.path.normpath(source)
	# dst = os.path.normpath(destination)
	src = translate_path(source)
	dst = translate_path(destination)

	if os.environ['IC_OS'] == "win":
		# If destination is a folder, append the filename from the source
		if os.path.isdir(dst):
			filename = os.path.basename(src)
			dst = os.path.join(dst, filename)

		# Delete the destination file if it already exists - this is to mimic
		# the Unix behaviour and force creation of the hard link
		if os.path.isfile(dst):
			# os.system('del "%s" /f /q' % dst)
			remove(dst)

		# Create the hardlink
		# cmd_str = 'mklink /H "%s" "%s"' %(dst, src)  # This only works with local NTFS volumes
		cmd_str = 'fsutil hardlink create "%s" "%s" >nul' % (dst, src)  # Works over SMB network shares; suppressing output to null

	else:
		cmd_str = 'ln -f %s %s' % (src, dst)

	verbose.detail(cmd_str)
	os.system(cmd_str)

	# Make sure source and destination files match
	if verify:
		if verify_hardlink(src, dst):
			return dst
		else:
			verbose.warning("Failed to create hardlink. Attempting to copy file instead.")
			copy(src, dst)
	else:
		return dst


def verify_hardlink(src, dst):
	"""Compare os.stat() for src and dst files to check for hardlink."""

	try:
		if os.stat(src) == os.stat(dst):
			return True
	except:
		pass

	return False


def remove(path, quiet=False):
	"""Remove files or folders recursively."""

	path = os.path.normpath(path)

	if not quiet:
		verbose.detail('remove "%s"' % path)
	try:
		if os.path.isfile(path):
			os.remove(path)
		elif os.path.isdir(path):
			shutil.rmtree(path)
		return True, path
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		msg = traceback.format_exception_only(exc_type, exc_value)[0]
		if not quiet:
			verbose.error(msg)
		return False, msg


def rename(source, destination, quiet=False):
	"""Rename a file or folder."""

	src = os.path.normpath(source)
	dst = os.path.normpath(destination)

	if not quiet:
		verbose.detail('rename "%s" -> "%s"' % (src, dst))
	try:
		os.rename(src, dst)
		return True, dst
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		msg = traceback.format_exception_only(exc_type, exc_value)[0]
		if not quiet:
			verbose.error(msg)
		return False, msg


def copy(source, destination, quiet=False):
	"""Copy a file or folder."""

	src = os.path.normpath(source)
	dst = os.path.normpath(destination)

	if not quiet:
		verbose.detail('copy "%s" -> "%s"' % (src, dst))
	try:
		shutil.copyfile(src, dst)
		return True, dst
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		msg = traceback.format_exception_only(exc_type, exc_value)[0]
		if not quiet:
			verbose.error(msg)
		return False, msg


def move(source, destination, quiet=False):
	"""Move a file or folder."""

	src = os.path.normpath(source)
	dst = os.path.normpath(destination)

	if not quiet:
		verbose.detail('move "%s" -> "%s"' % (src, dst))
	try:
		shutil.move(src, dst)
		return True
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		msg = traceback.format_exception_only(exc_type, exc_value)[0]
		if not quiet:
			verbose.error(msg)
		return False


def copy_tree(source, destination, quiet=False):
	"""Copy an entire directory tree.

	See https://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
	"""
	src = os.path.normpath(source)
	dst = os.path.normpath(destination)

	if not quiet:
		verbose.detail('copy tree "%s" -> "%s"' % (src, dst))
	try:
		for item in os.listdir(src):
			s = os.path.join(src, item)
			d = os.path.join(dst, item)
			if os.path.isdir(s):
				shutil.copytree(s, d, symlinks, ignore)
			else:
				shutil.copy2(s, d)
		return True
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		msg = traceback.format_exception_only(exc_type, exc_value)[0]
		if not quiet:
			verbose.error(msg)
		return False

	# if not quiet:
	# 	verbose.detail('copytree "%s" -> "%s"' % (src, dst))
	# try:
	# 	shutil.copytree(src, dst)
	# 	return True, dst
	# except:
	# 	exc_type, exc_value, exc_traceback = sys.exc_info()
	# 	msg = traceback.format_exception_only(exc_type, exc_value)[0]
	# 	if not quiet:
	# 		verbose.error(msg)
	# 	return False, msg


def set_hidden(path):
	"""Hide a file or folder (Windows only).

	Useful if the filename name starts with a dot, as these files are not
	automatically hidden on Windows.
	"""
	import ctypes
	FILE_ATTRIBUTE_HIDDEN = 0x02
	ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)


def walk(top, maxdepth):
	"""Scan through directories to a given recursion depth.

	See https://stackoverflow.com/a/35316298
	TODO: make Python 2.x compatible
	"""
	top = os.path.normpath(top)
	dirs, nondirs = [], []
	for entry in os.scandir(top):
		(dirs if entry.is_dir() else nondirs).append(entry.path)
	yield top, dirs, nondirs
	if maxdepth > 1:
		for path in dirs:
			for x in walk(path, maxdepth-1):
				yield x


def absolute_path(relPath, stripTrailingSlash=False):
	"""Convert a relative path to an absolute path.

	Expand environment variables in supplied path and replace backslashes with
	forward slashes for compatibility.
	If 'stripTrailingSlash' is True, remove trailing slash(es) from returned
	path.
	"""
	if relPath:
		if stripTrailingSlash:
			return os.path.normpath(os.path.expandvars(relPath)).replace("\\", "/").rstrip('/')
		else:
			return os.path.normpath(os.path.expandvars(relPath)).replace("\\", "/")
	else:
		return ""


def relative_path(absPath, token, tokenFormat='standard'):
	"""Convert an absolute path to a relative path.

	'token' is the name of an environment variable to replace.
	'tokenFormat' specifies the environment variable format:
		standard:   $VAR
		bracketed:  ${VAR}
		windows:    %VAR%
		nuke (TCL): [getenv VAR]
	"""
	try:
		if tokenFormat == 'standard':
			formattedToken = '$%s' % token
		elif tokenFormat == 'bracketed':
			formattedToken = '${%s}' % token
		elif tokenFormat == 'windows':
			formattedToken = '%%%s%%' % token
		elif tokenFormat == 'nuke':
			formattedToken = '[getenv %s]' % token
		else:
			formattedToken = ''

		# Ensure backslashes from Windows paths are changed to forward slashes
		envVar = os.environ[token].replace('\\', '/')
		relPath = absPath.replace('\\', '/')

		# Change to relative path
		relPath = relPath.replace(envVar, formattedToken)

		return os.path.normpath(relPath).replace("\\", "/")

	except:
		return os.path.normpath(absPath).replace("\\", "/")


def translate_path(path):
	"""Translate a path using rules for cross-platform support.

	TODO: fail gracefully if prefs file not found
	"""
	try:
		with open(os.environ['IC_GLOBALS'], 'r') as f:
			global_prefs = json.load(f)

		path_tr = path

		for rule in global_prefs.get('translation').get('rules'):
			if os.environ['IC_OS'] == "win":  # Windows
				if path.startswith(rule['mac']):
					path_tr = path.replace(rule['mac'], rule['win'], 1)
				elif path.startswith(rule['linux']):
					path_tr = path.replace(rule['linux'], rule['win'], 1)
				# Append trailing slash to Windows drive letter
				if path_tr.endswith(":"):
					path_tr += "\\" #os.sep
			elif os.environ['IC_OS'] == "mac":  # macOS
				if path.startswith(rule['win']):
					path_tr = path.replace(rule['win'], rule['mac'], 1)
				elif path.startswith(rule['linux']):
					path_tr = path.replace(rule['linux'], rule['mac'], 1)
			else:  # Linux
				if path.startswith(rule['win']):
					path_tr = path.replace(rule['win'], rule['linux'], 1)
				elif path.startswith(rule['mac']):
					path_tr = path.replace(rule['mac'], rule['linux'], 1)

		if path != path_tr:
			verbose.detail("Performing path translation:\n  from: %s\n    to: %s\n" % (path, absolute_path(path_tr)))

		return absolute_path(path_tr)

	except (AttributeError, IOError, KeyError, TypeError, ValueError):
		return path


def convert_unc_path_to_drive(path):
	"""Convert a UNC path to a mapped drive letter (Windows only).

	TODO: fail gracefully if prefs file not found
	"""
	if os.environ['IC_OS'] != "win":
		return path

	try:
		with open(os.environ['IC_GLOBALS'], 'r') as f:
			global_prefs = json.load(f)

		path = absolute_path(path)
		path_tr = path

		for key, value in global_prefs.get('drives').get('mappings').items():
			if path.startswith(value):  
				path_tr = path.replace(value, key, 1)
				# Append trailing slash to Windows drive letter
				if path_tr.endswith(":"):
					path_tr += "\\" #os.sep

		if path != path_tr:
			verbose.detail("Converting UNC path:\n  from: %s\n    to: %s\n" % (path, path_tr))

		return path_tr

	except (AttributeError, IOError, KeyError, TypeError, ValueError):
		return path


def check_illegal_chars(path, pattern=r'[^\w\.-]'):
	"""Check path for illegal characters, ignoring delimiter characters such
	as / \ : etc.
	Returns True if no illegal characters are found.
	"""
	clean_str = re.sub(r'[/\\]', '', os.path.splitdrive(path)[1])
	if re.search(pattern, clean_str) is None:
		return True
	else:
		return False


def sanitize(instr, pattern=r'\W', replace=''):
	"""Sanitize characters in string.

	Default removes all non-alphanumeric characters.
	"""
	return re.sub(pattern, replace, instr)
