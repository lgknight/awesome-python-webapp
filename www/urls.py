# -*- coding: utf8 -*-
# created time : 2016-08-29
__author__ = 'knight'

import re, hashlib

from transwarp.web import get, post, view, ctx
from models import User, Blog, Comment
from apis import api

_RE_EMAIL = re.compile(r'^[0-9a-zA-Z\.\-\_]+@[0-9a-zA-Z\-\_]+(\.[0-9a-zA-Z]+){1,4}$')
_RE_MD5 = re.compile(r'[0-9a-f]{32}$')

@view('blogs.html')
@get('/')
def index():
	blogs = Blog.find_all()
	# user = User.find_first("where email = ?", "123@123")
	return dict(blogs = blogs)

@api
@post('/api/users')
def register_user():
	i = ctx.request.input(name = '', email = '', password = '')
	name = i.name.strip()
	email = i.email.strip.lower()
	password = i.password
	if not name:
		raise APIValueError('name')
	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')
	if not password or not _RE_MD5.match(password):
		raise APIValueError('password')
	user = User.find_first('where email = ?', email)
	if user:
		raise APIError('register:failed', 'email', 'Email has already exist')
	user = User(name = name, email = email, password = password, image = "http://www.gravatar.com/avatar/%s?d=mm&s=120" %hashlib.md5(email).hexdigest())
	user.insert()
	return user

@view('register.html')
@get('/register')
def register():
	return dict()