from flask import session, abort, redirect, url_for
from functools import wraps


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('isAdmin'):
            return fn(*args,**kwargs)
        else:
            return redirect(url_for('main.adminLogin'))
    return wrapper


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('logined'):
            return fn(*args, **kwargs)
        else:
            abort(403)
    return wrapper
