from flask import Blueprint, abort

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("")
def index():
    abort(404)
