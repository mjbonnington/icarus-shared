#!/usr/bin/python

# shared/json_data.py
#
# Mike Bonnington <mjbonnington@gmail.com>
# (c) 2019-2021
#
# Class for handling generic JSON data files.
# Classes written to handle specific data files should inherit this class.


import os
import json

# Import custom modules
import verbose


class JSONData(object):
	""" Class for JSON data.
	"""
	def __init__(self, datafile=None):
		""" Initialise class. If datafile is not specified, create bare
			class. The data should then be loaded with the load() method.
		"""
		verbose.debug("%s" % self)

		self.dict = {}
		if datafile is not None:
			self.load(datafile)


	def load(self, datafile):
		""" Load data from datafile and store in a dictionary.
		"""
		self.datafile = os.path.normpath(datafile)
		return self.reload()


	def reload(self):
		""" Reload data from current datafile.
		"""
		if not os.path.isfile(self.datafile):
			verbose.detail('JSON file does not exist: "%s"' % self.datafile)
			return False

		try:
			with open(self.datafile, 'r') as f:
				self.dict = json.load(f)
			verbose.detail('JSON load: "%s"' % self.datafile)
			return True

		except IOError:
			verbose.warning('JSON file could not be read: "%s"' % self.datafile)
			return False

		# except json.decoder.JSONDecodeError:
		except ValueError:  # Fix for Python 2.x
			verbose.error('JSON file could not be parsed: "%s"' % self.datafile)
			return False


	def save(self):
		""" Save prefs dictionary to datafile.
		"""
		try:
			with open(self.datafile, 'w') as f:
				json.dump(self.dict, f, indent=4, sort_keys=True)
			verbose.detail('JSON save: "%s"' % self.datafile)
			return True

		except IOError:
			verbose.error('JSON file could not be written: "%s"' % self.datafile)
			return False


	def save_empty(self, datafile=None):
		""" Convenience function to save a blank datafile.
		"""
		if datafile is None:
			self.clear()
		else:
			self.datafile = os.path.normpath(datafile)
		return self.save()


	def merge(self, new_datafile):
		""" Merge in data from a new JSON file. Matching keys/values will be
			replaced with those from the new data.
		"""
		dict1 = self.dict.copy()  # Copy current dict
		if self.load(new_datafile):  # Load new datafile
			dict2 = self.dict.copy()  # Copy new dict
		else:
			dict2 = {}  # Create empty dict
			verbose.warning("Failed to merge metadata.")
		self.dict = dict(self.merge_dicts(dict1, dict2))  # Merge dicts


	def merge_dicts(self, dict1, dict2):
		""" Merge two dictionaries.
			See https://stackoverflow.com/a/7205672
		"""
		for k in set(dict1.keys()).union(dict2.keys()):
			if k in dict1 and k in dict2:
				if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
					yield (k, dict(self.merge_dicts(dict1[k], dict2[k])))
				elif isinstance(dict1[k], list) and isinstance(dict2[k], list):
					# Combine lists (TODO: sort / remove duplicates, etc.)
					yield (k, dict1[k]+dict2[k])
				else:
					# If one of the values is not a dict, you can't continue merging it.
					# Value from second dict overrides one in first and we move on.
					yield (k, dict2[k])
					# Alternatively, replace this with exception raiser to alert you of value conflicts
			elif k in dict1:
				yield (k, dict1[k])
			else:
				yield (k, dict2[k])


	def get_all_keys(self, var=None, path=None, delimiter='.'):
		"""	Return a list of keys from nested dictionary.
		"""
		if var is None:
			var = self.dict

		if hasattr(var, 'items'):
			for k, v in var.items():
				if path is None:
					keypath = k
				else:
					keypath = delimiter.join([path, k])
					yield keypath
				if isinstance(v, dict):
					for result in self.get_all_keys(v, keypath, delimiter):
						yield result


	def gen_dict_extract(self, key, var=None):
		"""	Search in nested dictionary.
			See https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
		"""
		if var is None:
			var = self.dict

		if hasattr(var, 'items'):
			for k, v in var.items():
				if k == key:
					yield v
				if isinstance(v, dict):
					for result in self.gen_dict_extract(key, v):
						yield result
				elif isinstance(v, list):
					for d in v:
						for result in self.gen_dict_extract(key, d):
							yield result


	def clear(self):
		""" Clear all data from the prefs dictionary.
		"""
		self.dict.clear()
