import sqlite3

from flask import Blueprint, request

bp = Blueprint("new", __name__)


@bp.route("/b")
def b():
    key = request.args.get("key", "")
    conn = sqlite3.connect(":memory:")
    return str(conn.execute("SELECT * FROM secrets WHERE k = '" + key + "'").fetchall())
