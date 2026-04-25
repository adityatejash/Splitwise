from flask import Blueprint

groups = Blueprint('groups', __name__)

from . import routes  # noqa
