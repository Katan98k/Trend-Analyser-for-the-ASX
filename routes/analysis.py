from flask import Blueprint, abort

analyse_bp = Blueprint("analyse", __name__)


@analyse_bp.route("")
def run_analysis():
    abort(404)
