#!/usr/bin/python

# shared/metadata.py
#
# Mike Bonnington <mjbonnington@gmail.com>
# (c) 2019-2020
#
# Manipulates JSON-based settings metadata for jobs, shots, assets, etc.


# Import custom modules
import json_data


class Metadata(json_data.JSONData):
	""" Class for settings metadata.
		Inherits JSONData class.
	"""
	def __init__(self, datafile=None):
		""" Allow datafile to be passed in on initialisation.
		"""
		super(Metadata, self).__init__(datafile)


	def get_attr(self, category, attr, default=None):
		""" Get a value from prefs dictionary. If the given value cannot be
			retrieved, and a default value is given, return default value.
		"""
		try:
			return self.dict[category][attr]

		except KeyError:
			if default is not None:  # Store default value
				try:
					self.dict[category][attr] = default
				except KeyError:
					self.dict[category] = {attr: default}
				return default
			else:
				return None


	def set_attr(self, category, attr, value):
		""" Set a value and store it in the prefs dictionary.
		"""
		try:
			self.dict[category][attr] = value
		except KeyError:
			self.dict[category] = {attr: value}


	def remove_attr(self, category, attr):
		""" Remove the given attribute from the prefs dictionary.
		"""
		return self.dict[category].pop(attr, None)
