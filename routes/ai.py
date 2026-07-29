from flask import Blueprint, abort

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("")
def ai_query():
    abort(404)
