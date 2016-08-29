# -*- coding: utf-8 -*-
# 编码方式必须声明为coding： 不能是coding :不能有空格

__author__ = 'knight'

import time, logging
import db

class Field(object):
	
	_count = 0

	def __init__(self, **kw):
		self.name = kw.get('name', None)
		# kw.get('name', None): if 'name' in kw.iterkeys() return kw['name'] else return None
		self._default = kw.get('default', None)
		self.primary_key = kw.get('primary_key', False)
		self.nullable = kw.get('nullable', False)
		self.updatable = kw.get('updatable', True)
		self.insertable = kw.get('insertabel', True)
		self.ddl = kw.get('ddl', '')
		self._order = Field._count
		self._count = Field._count + 1

	@property
	# 属性函数，f = Field()	f.default
	def default(self):
		d = self._default
		return d() if callable(d) else d


	def __str__(self):
		# print时使用， f = Field();	f <==> print f  f.__str__()转为字符串
		s = ['<%s : %s, %s, default(%s),' % (self.__class__.__name__, self.name, self.ddl, self._default)]
		self.nullable and s.append('N')
		# 相等于 if self.nullabel: s.append('N')
		self.updatable and s.append('U')
		self.insertable and s.append('I')
		s.append('>')
		return ''.join(s)

class StringField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = None
		if not 'ddl' in kw:
			kw['ddl'] = "varchar(255)"
		return super(StringField, self).__init__(**kw)

class IntegerField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = 0
		if not 'ddl' in kw:
			kw['ddl'] = "bigint"
		return super(IntegerField, self).__init__(**kw)

class FloatField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = 0.0
		if not 'ddl' in kw:
			kw['ddl'] = "real"
		return super(FloatField, self).__init__(**kw)

class BooleanField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = False
		if not 'ddl' in kw:
			kw['ddl'] = "bool"
		return super(BooleanField, self).__init__(**kw)

class TextField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = ''
		if not 'ddl' in kw:
			kw['ddl'] = 'text'
		return super(TextField, self).__init__(**kw)

class BlobField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = ''
		if not 'ddl' in kw:
			kw['ddl'] = 'blob'
		return super(BlobField, self).__init__(**kw)

class VersionField(Field):
	def __init__(self, name = None):
		return super(VersionField, self).__init__(name = name, default = 0, ddl = 'bigint')

# 创建数据库表时是否对表格预处理（插入， 更新， 删除等）
_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])


# 创建数据库表的sql语句
def _gen_sql(table_name, mappings):
	pk = None
	sql = ["create table %s (" %table_name]
	for f in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
		if not hasattr(f, 'ddl'):
			raise StandardError('no ddl in field %s', f)
		if f.primary_key:
			pk = f.name
		sql.append(f.nullable and ' %s %s,' %(f.name, f.ddl) or ' %s %s not null,' %(f.name, f.ddl))
	sql.append('primary key (%s));' %pk)
	return '\n'.join(sql)


class ModelMetaclass(type):

	def __new__(cls, name, bases, attrs):
	# __new__ 是在__init__之前被调用的特殊方法
    # __new__是用来创建对象并返回之的方法
    # 而__init__只是用来将传入的参数初始化给对象
    # 你很少用到__new__，除非你希望能够控制对象的创建
    # 这里，创建的对象是类，我们希望能够自定义它，所以我们这里改写__new__
    # 如果你希望的话，你也可以在__init__中做些事情
    # 还有一些高级的用法会涉及到改写__call__特殊方法，但是我们这里不用
		

		# print '*' * 50
		# print 'cls: %s' %cls
		# print 'name: %s' %name
		# print 'bases: %s' %bases
		# print 'attrs: %s' %attrs
		# print '*' * 50

		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)

		if not hasattr(cls, 'subclasses'):
			cls.subclasses = {}

		if not name in cls.subclasses:
			cls.subclasses[name] = name
		else:
			logging.warnning('Redefine class %s' % name)

		logging.info("Scan ORMmapping... %s " % name)

		mappings = dict()
		primary_key = None

		for k, v in attrs.iteritems():
			if isinstance(v, Field):
				if not v.name:
					v.name = k
				logging.info('Found Map : %s => %s' %(k, v))
				if v.primary_key:
					if primary_key:
						raise TypeError('Cannot define more than one primary_key...')
					if v.updatable:
						logging.warning('Note: change primary_key to non-updatable')
						v.updatable = False
					if v.nullable:
						logging.warning('Node: change primary_key to non-nullable')
					primary_key = v
				mappings[k] = v

		if not primary_key:
			raise TypeError('primary_key not defined in class: %s' % name)

		for k in mappings.iterkeys():
			attrs.pop(k)

		if not '__table__' in attrs:
			attrs['__table__'] = name.lower()

		attrs['__mappings__'] = mappings
		attrs['__primary_key__'] = primary_key
		attrs['__sql__'] = lambda self : _gen_sql(attrs['__table__'], mappings)
		
		for trigger in _triggers:
			if not trigger in attrs:
				attrs[trigger] = None
		
		return type.__new__(cls, name, bases, attrs)



class Model(dict):

	__metaclass__ = ModelMetaclass
	# 你首先写下class Foo(object)，但是类对象Foo还没有在内存中创建。Python会在类的定义中寻找__metaclass__属性，
	# 如果找到了，Python就会用它来创建类Foo，如果没有找到，就会用内建的type来创建这个类。

	def __init__(self, **kw):
		# print '*' * 30
		# for k, v in kw.iteritems():
		# 	print k, v
		# print '*' * 30
		
		super(Model, self).__init__(**kw)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError("object has no attribute %s" % key)

	def __setattr__(self, key, value):
		self[key] = value

	@classmethod
	# class T(): @classmethod	def fun():pass	T.fun()
	def get(cls, pk):
		# db 为全局模块，create_engine只用调用一次
		d = db.select_one('select * from %s where %s = ?' %(cls.__table__, cls.__primary_key__.name), pk)
		return cls(**d) if d else None

	@classmethod
	def find_all(cls, *args):
		L = db.select('select * from %s' %cls.__table__)
		return [cls(**d) for d in L]

	def insert(self):
		self.pre_insert and self.pre_insert()
		params = {}
		for k, v in self.__mappings__.iteritems():
			if v.insertable:
				if not hasattr(self, k):
					setattr(self, k, v.default)
				params[v.name] = getattr(self, k)
		db.insert('%s' % self.__table__, **params)
		return self

	@classmethod
	def find_first(cls, where, *args):
		d = db.select_one('select * from %s %s' %(cls.__table__, where), *args)
		return cls(**d) if d else None


if '__main__' == __name__:

	import doctest
	doctest.testmod()

