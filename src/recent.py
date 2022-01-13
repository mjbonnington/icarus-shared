#!/usr/bin/python

# recent.py
#
# Mike Bonnington <mjbonnington@gmail.com>
# (c) 2015-2021
#
# Manage recent lists (shots, files, etc.)


import os

# Import custom modules
import json_data
import verbose


class Recent(json_data.JSONData):
	"""Class for storing and manipulating recent lists.

	Inherits JSONData class.
	"""
	def __init__(self, datafile, key='default'):
		super(Recent, self).__init__(datafile)
		self.key = key


	def put(self, new_entry, key=None):
		"""Add an entry to the recent list and save file to disk.

		Keyword arguments:
		key -- if specified, use instead of self.key
		"""
		if key is None:
			key = self.key

		try:
			recentlist = self.dict[key]
		except KeyError:
			recentlist = []  # Clear recent list

		# If entry already exists in list, delete it
		if new_entry in recentlist:
			recentlist.remove(new_entry)

		# Prepend entry to list
		recentlist.insert(0, new_entry)

		# Limit list to specific size
		while len(recentlist) > int(os.environ.get('IC_NUMRECENTFILES', 10)):
			recentlist.pop()

		# Create data structure
		self.dict[key] = recentlist

		# Write to disk
		if self.save():
			verbose.detail("Added %s to recent list." % new_entry)
		else:
			verbose.warning("Entry %s could not be added to recent list." % new_entry)


	def get(self, last=False, key=None):
		"""Read recent list and return list.

		Keyword arguments:
		last (bool) -- if True return last entry only.
		key -- if specified, use instead of self.key
		"""
		if key is None:
			key = self.key
		# key = key.lower()  # Make key case-insensitive - disabled as it breaks shots with capitals

		try:
			recentlist = self.dict[key]

			# Slice the list to specific size
			recentlist = recentlist[:int(os.environ.get('IC_NUMRECENTFILES', 10))]

			if last:
				return recentlist[0]
			else:
				return recentlist

		except (KeyError, IndexError) as e:
			verbose.debug(str(e))
			return []
