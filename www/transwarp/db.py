# -*- coding: utf-8 -*-

__author__ = 'knight'
# update time: 2016/08/10


import threading, functools, logging
logging.basicConfig(level = logging.DEBUG)

class _Engine(object):
	def __init__(self,connect):
		self.connect = connect
	def connect(self):
		return self.connect

engine = None

class Dict(dict):
	def __init__(self, keys = (), values = (), **kw):
		super(Dict, self).__init__(**kw)
		for k, v in zip(keys, values):
			self[k] = v
	
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError("Dict object has no Attribute %s" %key)

	def __setattr__(self, key, value):
		self[key] = value


def create_engine(user, password, database, host = '127.0.0.1', port = 3306, **kw):
	import MySQLdb
	global engine
	if engine is not None:
		raise DBError('engine is not none')
	params = dict(user = user, passwd = password, db = database, host = host, port = port)
	# defalt = dict(user_unicode = True, charset = 'utf8', collation = 'utf8_general_ci', autocommit = False)
	defalt = dict(charset = 'utf8', autocommit = False)
	for k, v in defalt.iteritems():
		params[k] = kw.pop(k, v)
	params.update(kw)
	# params['buffered'] = True
	engine = _Engine(lambda : MySQLdb.connect(**params))
	logging.info('init db engine is ok')


class _Lasyconnection(object):
	def __init__(self):
		self.connection = None
	
	def cursor(self):
		if self.connection is None:
			connection = engine.connect()
			logging.info('connection open.')
			self.connection = connection
		return self.connection.cursor()

	def commit(self):
		self.connection.commit()

	def rollback(slef):
		self.connection.rollback()

	def cleanup(self):
		if self.connection:
			connection = self.connection
			self.connection = None
			connection.close()
			logging.info('connection close.')

class _DBCtx(threading.local):
	def __init__(self):
		self.connection = None
		self.transactions = 0
	
	def is_init(self):
		return not self.connection is None
	
	def init(self):
		self.connection = _Lasyconnection()
		self.transaction = 0

	def cleanup(self):
		self.connection.cleanup()
		self.connection = None

	def cursor(self):
		return self.connection.cursor()

_db_ctx = _DBCtx()

class _ConnectionCtx(object):
	def __enter__(self):
		global _db_ctx
		self.should_cleanup = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_cleanup = True
		return self

	def __exit__(self,exctype,excvalue,traceback):
		global _db_ctx
		if self.should_cleanup:
			_db_ctx.cleanup()

def connection():
	return _ConnectionCtx()

def with_connection(func):
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		with connection():
			return func(*args, **kw)
	return _wrapper

class _TransactionCtx(object):
	def __enter__(self):
		global _db_ctx
		self.should_close_con = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_close_con = True
		_db_ctx.transactions += 1
		logging.info('begin transactions' if 1 == _db_ctx.transactions else 'join another transactions...')

	def __exit__(self, exctype, excvalue, traceback):
		global _db_ctx
		_db_ctx.transactions -= 1
		try:
			if 0 == _db_ctx.transactions:
				if exctype is None:
					self.commit()
				else:
					self.rollback()
		finally:
			if self.should_close_con:
				_db_ctx.cleanup()

	def commit(self):
		global _db_ctx
		logging.info("commit transactions...")
		try:
			_db_ctx.connection.commit()
			logging.info("commit success")
		except:
			logging.warning('commit failed. try rollback')
			_db_ctx.connection.rollback()
			logging.warning('rollback')
			raise

	def rollback(self):
		global _db_ctx
		logging.warning('rollback transactions...')
		_db_ctx.connection.rollback()
		logging.info('rollback ok.')

def transcation():
	return _TransactionCtx()

def with_transcation(func):
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		with transcation():
			return func(*args, **kw)
	return _wrapper

@with_connection
def _select(sql, first = True, *args):
	global _db_ctx
	sql = sql.replace('?', '%s')
	logging.info('sql : %s, args: %s' %(sql, args))
	cursor = None
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		if cursor.description:
			keys = [x[0] for x in cursor.description]
		if first:
			values = cursor.fetchone()
			if not values:
				return None
			return Dict(keys, values)
		return [Dict(keys, x) for x in cursor.fetchall()]
	finally:
		if cursor:
			cursor.close()

def select_one(sql, *args):
	return _select(sql, True, *args)

def select(sql, *args):
	return _select(sql, False, *args)

@with_connection
def _update(sql, *args):
	global _db_ctx
	sql = sql.replace('?', '%s')
	logging.info('sql : %s, args: %s' %(sql, args))
	cursor = None
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		rowcount = cursor.rowcount
		if not _db_ctx.transactions:
			logging.info('transactions commit...')
			_db_ctx.connection.commit()
		return rowcount
	finally:
		if cursor:
			cursor.close()

def update(sql, *args):
	return _update(sql, *args)

def insert(table, **kw):
	# z = zip(x, y)  
	# x, y = zip(*z)
	cols, args = zip(*kw.iteritems())
	sql = "insert into %s (%s) values (%s)" %(table, ','.join(['%s' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
	return _update(sql, *args)

if '__main__' == __name__:
	logging.basicConfig(level = logging.DEBUG)
