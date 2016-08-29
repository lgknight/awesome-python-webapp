from transwarp.web import get, view
from models import User, Blog, Comment

@view('blogs.html')
@get('/')
def index():
	
    blogs = Blog.find_all()

    user = User.find_first("where email = ?", "123@123")
    
    return dict(blogs = blogs, user = user)
