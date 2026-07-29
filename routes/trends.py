from flask import Blueprint, abort

trend_bp = Blueprint("trend", __name__)


@trend_bp.route("")
def view_trends():
    abort(404)
