from flask import session, abort, redirect, url_for
from functools import wraps
import logging


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
            return redirect(url_for('main.login'))
    return wrapper

def print_func_info(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        logging.basicConfig(level=logging.INFO)
        logging.info(fn.__name__)
        return fn(*args,**kwargs)
    return wrapper