from flask import Blueprint, g

main = Blueprint('main', __name__)

from . import forms, views
