from . import main
from flask import render_template


@main.app_errorhandler(403)
def no_access(e):
    return render_template('403.html'), 403


@main.app_errorhandler(404)
def page_no_found(e):
    return render_template('404.html'), 404
