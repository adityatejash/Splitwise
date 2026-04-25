from flask import Blueprint

expenses = Blueprint('expenses', __name__)

from . import routes  # noqa
