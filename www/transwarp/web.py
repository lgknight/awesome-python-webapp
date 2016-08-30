# -*- coding: utf8 -*-

__author__ = 'knight'

# update time: 2016-08-17

import logging, cgi, urllib, re, datetime, threading, sys, os, functools, types, mimetypes, traceback
from StringIO import StringIO
ctx = threading.local()


class Dict(dict):
	def __init__(self, keys = (), values = (), **kw):
		super(Dict, self).__init__(**kw)
		for k, v in zip(keys, values):
			self[k] = v

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(" 'Dict' Object has no key %s" % key)

	def __setattr__(self, key, value):
		self[key] = value

def _to_str(value):
	if isinstance(value, str):
		return value
	if isinstance(value, unicode):
		return value.encode('utf-8')
	return str(value)

def _to_unicode(value, encoding = 'utf-8'):
	return value.decode(encoding)


def _quote(s, encoding = 'utf-8'):
	if isinstance(s, unicode):
		s = s.encode(encoding)
	return urlllib.quote(s)

def _unquote(s, encoding = 'utf-8'):
	return urllib.unquote(s).decode(encoding)
	
_RESPONSE_STATUS = {
	# Informational
	100: 'Continue',
	101: 'Switching Protocols',
	102: 'Processing',

	# Successful
	200: 'OK',
	201: 'Created',
	202: 'Accepted',
	203: 'Non-Authoritative Information',
	204: 'No Content',
	205: 'Reset Content',
	206: 'Partial Content',
	207: 'Multi Status',
	226: 'IM Used',

	# Redirection
	300: 'Multiple Choices',
	301: 'Moved Permanently',
	302: 'Found',
	303: 'See Other',
	304: 'Not Modified',
	305: 'Use Proxy',
	307: 'Temporary Redirect',

	# Client Error
	400: 'Bad Request',
	401: 'Unauthorized',
	402: 'Payment Required',
	403: 'Forbidden',
	404: 'Not Found',
	405: 'Method Not Allowed',
	406: 'Not Acceptable',
	407: 'Proxy Authentication Required',
	408: 'Request Timeout',
	409: 'Conflict',
	410: 'Gone',
	411: 'Length Required',
	412: 'Precondition Failed',
	413: 'Request Entity Too Large',
	414: 'Request URI Too Long',
	415: 'Unsupported Media Type',
	416: 'Requested Range Not Satisfiable',
	417: 'Expectation Failed',
	418: "I'm a teapot",
	422: 'Unprocessable Entity',
	423: 'Locked',
	424: 'Failed Dependency',
	426: 'Upgrade Required',

	# Server Error
	500: 'Internal Server Error',
	501: 'Not Implemented',
	502: 'Bad Gateway',
	503: 'Service Unavailable',
	504: 'Gateway Timeout',
	505: 'HTTP Version Not Supported',
	507: 'Insufficient Storage',
	510: 'Not Extended',

	
}	

class HttpError(Exception):
	def __init__(self, code):
		super(HttpError, self).__init__()
		self.status = '%d %s' %(code, _RESPONSE_STATUS[code])

	def header(self, name, value):
		if not hasattr(self, '_headers'):
			self._headers = [_HEADER_X_POWERED_BY]
		self._headers.append((name, value))

	@property 
	def headers(self):
		# return self._headers if hasattr(self, '_headers') else []
		return hasattr(self, '_headers') and self._headers or []

	def __str__(self):
		return self.status

	__repr__ = __str__

class RedirectError(HttpError):
	def __init__(self, code, location):
		super(RedirectError, self).__init__(code)
		self.location = location

	def __str__(self):
		return '%s %s' %(self.status, self.location)

	__repr__ = __str__

def badrequest():
	return HttpError(400)

def unauthorized():
	return HttpError(401)

def forbidden():
	return HttpError(403)

def notfound():
	return HttpError(404)

def conflict():
	return HttpError(409)

def internalerror():
	return HttpError(500)

def redirect(location):
	return RedirectError(301, location)

def found(location):
	return RedirectError(302, location)

def seeother(location):
	return RedirectError(303, location)

def get(path):
	def wrapper(func):
		func.__web_route__ = path
		func.__web_method__ = 'GET'
		return func
	return wrapper

def post(path):
	def wrapper(func):
		func.__web_route__ = path
		func.__web_method__ = 'POST'
		return func
	return wrapper

_re_route = re.compile(r'(\:[a-zA-Z_]\w*)')

def _build_regex(path):
	re_list = ['^']
	var_list = []
	is_var = False
	for v in _re_route.split(path):
		if is_var:
			var_name = v[1:]
			var_list.append(var_name)
			re_list.append(r'(?P<%s>[^\/]+)' %var_name)
		else:
			s = ''
			for ch in v:
				if ch >= '0' and ch <= '9':
					s = s + ch
				elif ch >= 'a' and ch <= 'z':
					s = s + ch
				elif ch >= 'A' and ch <= 'Z':
					s = s + ch
				else:
					s = s + '\\' + ch
			re_list.append(s)
		is_var = not is_var
	re_list.append('$')
	return ''.join(re_list)


# 请求地址+请求处理函数
class Route(object):
	def __init__(self, func):
		self.path = func.__web_route__
		self.method = func.__web_method__
		self.is_static = _re_route.search(self.path) is None
		if not self.is_static:
			self.route = re.compile(_build_regex(self.path))
		self.func = func

	def match(self, url):
		return self.route.match(url) and m.groups() or None

	def __call__(self, *args):
		return self.func(*args)

def _static_file_generator(fpath):
	block_size = 8192
	with file.open(fpath, 'rb') as f:
		block = f.read(block_size)
		while block:
			yield block
			block = f.read(block_size)

class StaticFileRoute(object):
	def __init__(self):
		self.method = 'GET'
		self.is_static = 'False'
		self.route = re.compile('^/static/(.+)$')

	def match(self, url):
		if url.startswith('/static/'):
			return (url[1:])
		return None

	def __call__(self, *args):
		fpath = os.path.join(ctx.application.document_root, args[0])
		print fpath
		if not os.path.isfile(fpath):
			raise notfound()
		fext = os.path.splitext(fpath)[0]
		ctx.reponse.content_type = mimetypes.types_map.get(fext.lower(), 'application/cotet-stream')
		return _static_file_generator(fpath) 

class MultipartFile():
	def __init__(self, storage):
		self.filename = _to_unicode(storage.filename)
		self.file = storage.file


def favicon_handler():
	return static_favicon_handler('/favicon.ico')


class Request(object):
	
	def __init__(self, environ):
		self._environ = environ

	def _parse_input(self):
		def _convert(item):
			if isinstance(item, list):
				return [_to_unicode(i.value) for i in item]
			if item.filename:
				return MultipartFile(item)
			return _to_unicode(item.value)

		fs = cgi.FieldStorage(fp = self._environ['wsgi.input'], environ = self._environ, keep_blank_values = True)
		inputs = {}
		for key in fs:
			inputs[key] = _convert(fs[key])
		return inputs

	def _get_raw_input(self):
		# 获取输入表单
		# 结果返回字典:值为：Unicode或list或MultipartFile。
		if not hasattr(self, '_raw_input'):
			self._raw_input = self._parse_input()
		return self._raw_input

	def __getitem__(self, key):
		r = self._get_raw_input()[key]
		return r[0] if isinstance(r, list) else r
		# if isinstance(r, list):
		# 	return r[0]
		# return r

	def get(self, key, default = None):
		r = self._get_raw_input().get(key, default)
		# >>> x = {'a':1}
		# >>> x.get('a')
		# 1
		# >>> x.get('a','N')
		# 1
		# >>> x.get('b','N')
		# 'N'
		return r[0] if isinstance(r, list) else r

		# if isinstance(r, list):
		# 	return r[0]
		# return r

	def gets(self, key):
		r = self._get_raw_input()[key]
		return r if isinstance(r, list) else [r]
		# if isinstance(r, list):
		# 	return r
		# return [r]

	def input(self, **kw):
		copy = Dict(**kw)
		raw = self._get_raw_input()
		for k, v in raw.iteritems():
			copy[k] = v[0] if isinstance(v, list) else v
		return copy

	def getbody(self):
		fp = self._environ('wsgi:input')
		return fp.read()

	@property
	def remote_addr(self):
		return self._environ.get('REMOTE_ADDR', '0.0.0.0')

	@property
	def document_root(self):
		return self._environ.get('DOCUMENT_ROOT', '')

	@property
	def query_string(self):
		return self._environ.get('QUERY_STRING', '')

	@property
	def environ(self):
		return self._environ

	@property 
	def request_method(self):
		return self._environ['REQUEST_METHOD']

	@property 
	def path_info(self):
		return urllib.unquote(self._environ.get('PATH_INFO', ''))
		# >>> s = "url%20=%20%2F&email=qq"
		# >>> print urllib.unquote(s)
		# url = /&email=qq
	
	@property 
	def host(self):
		return self._environ.get('HTTP_HOST','')

	def _get_headers(self):
		if not hasattr(self, '_headers'):
			hdrs = {}
			for k, v in self._environ.iteritems():
				if k.startswith('HTTP_'):
					hdrs[k[5:].replace('_','-').upper()] = v.decode('utf-8')
			self._headers = hdrs
		return self._headers

	@property 
	def headers(self):
		return dict(**self._get_headers())

	def header(self, head, default):
		return self._get_headers().get(head.upper(), default)

	def _get_cookies(self):
		if not hasattr(self, '_cookies'):
			cks = {}
			cks_str = self._environ.get('HTTP_COOKIE')
			if cks_str:
				for cs in cks_str.split(';'):
					pos = cs.find('=')
					if pos > 0:
						cks[cs[:pos].strip()] = _unqoute(cs[pos + 1:])
						# 删除开头和结尾处'', '\t', '\n', '\r'
						# >> string = ' 12\n34\t\r'
						# >>> string.strip()
						# '12\n34'
			self._cookies = cks
		return self._cookies

	@property 
	def cookies(self):
		return dict(**self._get_cookies())

	def cookie(self, name, default):
		return self._get_cookies.get(name.upper(), default)

_RESPONSE_HEADER = (
	'Accept-Ranges',
	'Age',
	'Allow',
	'Cache-Control',
	'Connection',
	'Content-Encoding',
	'Content-Language',
	'Content-Length',
	'Content-Location',
	'Content-MD5',
	'Content-Disposition',
	'Content-Range',
	'Content-Type',
	'Date',
	'ETag',
	'Expires',
	'Last-Modified',
	'Link',
	'Location',
	'P3P',
	'Pragma',
	'Proxy-Authenticate',
	'Refresh',
	'Retry-After',
	'Server',
	'Set-Cookie',
	'Strict-Transport-Security',
	'Trailer',
	'Transfer-Encoding',
	'Vary',
	'Via',
	'Warning',
	'WWW-Authenticate',
	'X-Frame-Options',
	'X-XSS-Protection',
	'X-Content-Type-Options',
	'X-Forwarded-Proto',
	'X-Powered-By',
	'X-UA-Compatible'
	)

_RESPONSE_HEADER_DICT = dict(zip(map(lambda x : x.upper(), _RESPONSE_HEADER), _RESPONSE_HEADER))

_HEADER_X_POWERED_BY = ('X_POWERED_BY', 'transwarp/1.0')

_TIMEDELTA_ZERO = datetime.timedelta(0)

_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')

class UTC(datetime.tzinfo):
	def __init__(self, utc):
		utc = utc.strip().upper()
		ft = _RE_TZ.match(utc)
		if ft:
			minus = ft.group(1) == '-'
			h = int(ft.group(2))
			m = int(ft.group(3))
			if minus:
				h = -h
				m = -m
			self._utcoffset = datetime.timedelta(hours = h, minutes = m)
			self._tzname = 'UTC=%s' %utc
		else:
			raise ValueError('bad utc format')

	def utfoffset(self):
		return self._utcoffset

	def dst(self):
		return _TIMEDELTA_ZERO

	def tzname(self):
		return self._tzname

	def __str__(self):
		return 'UTC object %s' %self._tzname

	__repr__ = __str__


UTC_0 = UTC('+00:00')

_RE_RESPONSE_STATUS = re.compile('^\d\d\d( [\w ]+)?$')

class Response(object):
	def __init__(self):
		self._status = '200 OK'
		self._headers = {'CONTENT-TYPE' : 'text/html;charset=utf-8'}

	@property 
	def headers(self):
		L = [(_RESPONSE_HEADER_DICT.get(k,k), v) for k, v in self._headers.iteritems()]
		if hasattr(self, '_cookies'):
			for v in self._cookies.itervalues():
				L.append('SET_COOKIE', v)
		L.append(_HEADER_X_POWERED_BY)
		return L

	def header(self, name):
		key = name.upper()
		if not key in _RESPONSE_HEADER_DICT:
			key = name
		return self._headers.get(key)

	def unset_header(self, name):
		key = name.upper()
		if key not in _RESPONSE_HEADER_DICT:
			key = name
		if key in self._headers:
			del self._headers[key]

	def set_header(self, name, value):
		key = name.upper()
		if key not in _RESPONSE_HEADER_DICT:
			key = name
		self._headers[key] = _to_str(value)

	@property 
	def content_type(self):
		return self.header('CONTENT-TYPE')

	@content_type.setter
	def content_type(self, value):
		if value:
			self.set_header('CONTENT-TYPE', value)
		else:
			self.unset_header('CONTENT-TYPE')

	@property 
	def content_length(self):
		return self.header('CONTENT-LEHGTN')

	@content_length.setter
	def content_length(self, value):
		if value:
			self.set_header('CONTENT-LEHGTN', value)
		else:
			self.unset_header('CONTENT-LEHGTN')

	def set_cookie(self, name, value, max_age = None, expires = None, path = '/', domin = None, secure = False, http_only = True):
		if not hasattr(self, '_cookies'):
			self._cookies = {}
		L = ['%s=%s' %(_quote(name), _quote(value))]
		if expires is not None:
			if isinstance(expires, (float, int , long)):
				L.append('Expires=%s' %(datetime.datetime.fromtimestamp(expires, UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT')))
			if isinstance(expires, (datetime.date, datetime.datetime)):
				L.append('Expires=%s' %(datetime.datetime.astimezone(expires).strftime('%a, %d-%b-%Y %H:%M:%S GMT')))
		if isinstance(max_age, (int, long)):
			L.append('Max-Age=%d' %max_age)
		L.append('Path=%s' %path)
		if domin:
			L.append('Domin=%s' %domin)
		if secure:
			L.append('Secure')
		if http_only:
			L.append('HttpOnly')
		self._cookies[name] = ' ;'.join(L)

	def delete_cookie(self, name):
		self.set_cookie(name, '__delete__', expires = None)

	def unset_cookie(self, name):
		if hasattr(self, '_cookies'):
			if name in self._cookies:
				del self._cookies[name]
	@property 
	def status_code(self):
		return int(self._status[:3])

	@property 
	def status(self):
		return self._status

	@status.setter
	def status(self, value):
		if isinstance(value, (int, long)):
			if value >= 100 and value <= 999:
				st = _RESPONSE_STATUS.get(value, '')
				if st:
					self._status = '%d %s' %(value, st)
				else:
					self._status = str(value)
			else:
				raise ValueError('bad Response code: %d' %value)
		elif isinstance(value, basestring):
			if isinstance(value, unicode):
				value = value.encode('utf-8')
			if _RE_RESPONSE_STATUS.match(value):
				self._status = value
			else:
				raise ValueError('bad Response code: %d' %value)
		else:
			raise TypeError('bad type of response code.')

class Template(object):
	def __init__(self, template_name, **kw):
		self.template_name = template_name
		self.model = dict(**kw)

class TemplateEngine(object):
	def __call__(self, path, model):
		pass

class Jinja2TemplateEngine(TemplateEngine):
	def __init__(self, templ_dir, **kw):
		from jinja2 import Environment, FileSystemLoader
		if not 'autoescape' in kw:
			kw['autoescape'] = True
		self._env = Environment(loader = FileSystemLoader(templ_dir), **kw)

	def add_filter(self, name, fn_filter):
		self._env.filters[name] = fn_filter

	def __call__(self, path, model):
		return self._env.get_template(path).render(**model).encode('utf-8')

def _default_error_handler(e, start_response, is_debug):
	pass

def view(path):
	def _decorater(func):
		@functools.wraps(func)
		def _wrap(*args, **kw):
			r = func(*args, **kw)
			# print '+' * 50
			# print r
			if isinstance(r, dict):
				logging.info('return a Template')
				return Template(path, **r)
			raise ValueError('Except a dict value when using @view')
		# print '*' * 80 + path
		return _wrap
	return _decorater

_RE_INTERCEPTER_START_WITH = re.compile(r'^([^\*\?]+)\*?$')
_RE_INTERCEPTER_END_WITH = re.compile(r'^\*([^\*\?]+)$')

def _build_pattern_fn(patten):
	m = _RE_INTERCEPTER_START_WITH.match(patten)
	if m:
		return lambda p: p.startswith(m.group(1))
	m = _RE_INTERCEPTER_END_WITH(patten)
	if m:
		return lambda p: p.endswith(m.group(1))
	raise ValueError('invalid pattern')

def interceptor(pattern = '/'):
	def _decorater(func):
		func.__interceptor__ = _build_pattern_fn(pattern)
		return func
	return _decorater

def _build_interceptor_fn(func, next):
	def _wrap():
		if func.__interceptor__(ctx.request.path_info):
			return func(next)
		return next()
	return _wrap

def _build_interceptor_chain(last_fn, *interceptors):
	L = list(interceptors)
	L.reverse()
	lf = last_fn
	for f in L:
		lf = _build_interceptor_fn(f, lf)
	return lf

def _load_module(module_name):
	last_dot = module_name.rfind('.')
	if last_dot == (-1):
		return __import__(module_name, globals(), locals())
	from_module = module_name[:last_dot]
	import_module = module_name[last_dot + 1:]
	m = __import__(from_module, globals(), locals(),[import_module])
	return getattr(m, import_module)
	# m.import_module
	# use as import_module()...
	# >>> m = __import__('random', globals(),locals(),[randint])
	# >>> x = getattr(m, 'randint')
	# >>> x(1,10)
	# 7

class WSGIApplication(object):
	def __init__(self, document_root = None, **kw):
		self._running = False
		self._document_root = document_root
		self._interceptor = []
		self._template_engine = None
		self._get_static = {}
		self._post_static = {}
		self._get_dynamic = []
		self._post_dynamic = []

	def check_not_running(self):
		if self._running:
			raise RuntimeError('cannot modify wsgi when running...')

	@property 
	def template_engine(self):
		return self._template_engine

	@template_engine.setter		#w.template_engine = engine
	def template_engine(self, engine):
		self.check_not_running()
		self._template_engine = engine


	# 将urls 中的请求地址与相应的信息匹配
	def add_url(self, func):
		self.check_not_running()
		route = Route(func)
		if route.is_static:
			if route.method == 'GET':
				self._get_static[route.path] = route
			if route.method == 'POST':
				self._get_static[route.path] = route

		else:
			if route.method == 'GET':
				self._get_dynamic.append(route)
			if route.method == 'POST':
				self._get_dynamic.append(route)
		logging.info('Add route')

	# 添加urls中所有的url处理函数
	def add_module(self, mod):
		self.check_not_running()

		m = mod if type(mod) == types.ModuleType else _load_module(mod)
		# if type(mod) == types.ModuleType:
		# 	print 'module'
		# 	m = mod  
		# else:
		# 	print 'load_module'
		# 	m =  _load_module(mod)
		logging.info('load module %s' %m.__name__)
		for name in dir(m):
			fn = getattr(m, name)
			if callable(fn) and hasattr(fn, '__web_route__') and hasattr(fn, '__web_method__'):
				self.add_url(fn)

	def add_interceptor(self, func):
		self.check_not_running()
		self._interceptor.append(func)
		logging.info('add interceptor')

	def run(self, port = 9000, host = '127.0.0.1'):
		from wsgiref.simple_server import make_server
		logging.info('wsgi will start at %s:%d' %(host, port))
		server = make_server(host, port, self.get_wsgi_application(debug = True))
		server.serve_forever()

	def get_wsgi_application(self, debug = False):
		self.check_not_running()
		if debug:
			self._get_dynamic.append(StaticFileRoute())
		self.running = True
		_application = Dict(document_root = self._document_root)

		def fn_route():
			request_method = ctx.request.request_method
			path_info = ctx.request.path_info
			if request_method == 'GET':
				fn = self._get_static.get(path_info, None)
				if fn:
					return fn()
				for fn in self._get_dynamic:
					args = fn.match(path_info)
					if args:
						return fn(*args)
				raise notfound()
			if request_method == 'POST':
				fn = self._post_static.get(path_info, None)
				if fn:
					return fn()
				for fn in self._post_dynamic:
					args = fn.match(path_info)
					if args:
						return fn(*args)
				raise notfound()
			raise badrequest()
		
		fn_exec = _build_interceptor_chain(fn_route, *self._interceptor)
		
		def wsgi(env, start_response):
			# wsgi() 由WSGI服务器调用，env与start_response由WSGI填写
			ctx.application = _application
			# print ctx.application

			ctx.request = Request(env)
			response = ctx.response = Response()
			try:
				r = fn_exec()
				if isinstance(r, Template):
					r = self._template_engine(r.template_name, r.model)
				if isinstance(r, unicode):
					r = r.encode('utf-8')
				if r is None:
					r = []
				start_response(response.status, response.headers)
				return r
			except RedirectError, e:
				response.set_header('location', e.location)
				start_response(e.status, response.headers)
				return []
			except HttpError, e:
				start_response(e.status, response.headers)
				return ['<html><body><h1>', e.status ,'</h1></body></html>']
			except Exception, e:
				logging.exception(e)
				if not debug:
					start_response('500 internalerror',[])
					return ['<html><body><h1>500 internalerror</h1></body></html>']
				exc_type, exc_value, exc_traceback = sys.exc_info()
				fp = StringIO()
				traceback.print_exception(exc_type, exc_value, exc_traceback, file=fp)
				stacks = fp.getvalue()
				fp.close()
				start_response('500 Internal Server Error', [])
				return [
					r'''<html><body><h1>500 Internal Server Error</h1><div style="font-family:Monaco, Menlo, Consolas, 'Courier New', monospace;"><pre>''',
					stacks.replace('<', '&lt;').replace('>', '&gt;'),
					'</pre></div></body></html>']
			
			finally:
				del ctx.application
				del ctx.response
				del ctx.request
		return wsgi



if __name__ == '__main__':
	ws = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))
	ws.run()