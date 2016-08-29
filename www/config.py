# -*- encoding:utf8 -*-
# create time : 2016-08-20

__author__ = 'knight'

import config_default

class Dict(dict):
	def __init__(self, keys = (), values= (), **kw):
		super(Dict, self).__init__(**kw)
		for k, v in zip(keys, values):
			self[k] = v

	def __setattr__(self, k, v):
		self[k] = v

	def __getattr__(self, k):
		try:
			return self[k]
		except KeyError:
			raise AttributeError('object Dict has no attribute %s' %k)

def merge(default, override):
	r = {}
	for k, v in default.iteritems():
		if k in override:
			if isinstance(v, dict):
				r[k] = merge(v, override[k])
			else:
				r[k] = default[k]
		else:
			r[k] = v
	return r

def _toDict(d):
	D = Dict()
	for k, v in d.iteritems():
		D[k] = v if not isinstance(v, dict) else _toDict(v) 
	return D

configs = config_default.configs

try:
	import config_override
	configs = merge(configs, config_override.configs)
except ImportError:
	pass

configs = _toDict(configs)
