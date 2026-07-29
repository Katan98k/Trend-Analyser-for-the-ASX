from flask import Blueprint, abort

history_bp = Blueprint("history", __name__)


@history_bp.route("")
def list_history():
    abort(404)
