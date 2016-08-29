# # -*- coding: utf-8 -*-

# __author__ = 'knight'

# from transwarp import db
# db.create_engine(user = 'root', passwd = 'root', db = 'library')
# db.select("select * from book")

# import logging

# class ModelMetaclass(type):
#     '''
#     Metaclass for model objects.
#     '''
#     def __new__(cls, name, bases, attrs):
#         print name
#         # skip base Model class:
#         if name=='Model':

#             return type.__new__(cls, name, bases, attrs)

#         # store all subclasses info:
#         if not hasattr(cls, 'subclasses'):
#             cls.subclasses = {}
#         if not name in cls.subclasses:
#             cls.subclasses[name] = name
#         else:
#             logging.warning('Redefine class: %s' % name)

#         logging.info('Scan ORMapping %s...' % name)
#         mappings = dict()
#         primary_key = None
#         for k, v in attrs.iteritems():
#             if isinstance(v, int):
#                 if not v.name:
#                     v.name = k
#                 logging.info('Found mapping: %s => %s' % (k, v))
#                 # check duplicate primary key:
#                 if v.primary_key:
#                     if primary_key:
#                         raise TypeError('Cannot define more than 1 primary key in class: %s' % name)
#                     if v.updatable:
#                         logging.warning('NOTE: change primary key to non-updatable.')
#                         v.updatable = False
#                     if v.nullable:
#                         logging.warning('NOTE: change primary key to non-nullable.')
#                         v.nullable = False
#                     primary_key = v
#                 mappings[k] = v
#         # check exist of primary key:
#         if not primary_key:
#             raise TypeError('Primary key not defined in class: %s' % name)
#         for k in mappings.iterkeys():
#             attrs.pop(k)
#         if not '__table__' in attrs:
#             attrs['__table__'] = name.lower()
#         attrs['__mappings__'] = mappings
#         attrs['__primary_key__'] = primary_key
#         attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'], mappings)
#         for trigger in _triggers:
#             if not trigger in attrs:
#                 attrs[trigger] = None
#         return type.__new__(cls, name, bases, attrs)

# class Model(dict):
# 	__metaclass__ = ModelMetaclass
# 	def __init__(self):
# 		pass

# class User(Model):
# 	def __init__(self):
# 		pass

# u = User()


# from models import User
# from transwarp import db

# db.create_engine(user = 'root', passwd = 'root', db = 'awesome')

# u = User(name = 'ssTest', email = '1s23s@qq.com', password = 's123', image = 'sabout')
#print u.id
# print u
# u.insert()
# print u.id

# u2 = User.get('00147118804410202d1077733324818bd01d978c2020fcd000')
# print u2
# import os
# print os.path.abspath(__file__)
# print os.path.dirname(os.path.abspath(__file__))


# import urls
# import types

# if type(urls) == types.ModuleType:
# 	print 'get'



from transwarp.orm import Model, StringField

def next_id():
	pass

class TeMo(Model):
	id = StringField(primary_key = True, default = next_id(), ddl = 'varchar(50)')
