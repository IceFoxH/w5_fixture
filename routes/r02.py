import sqlite3
from flask import Blueprint, request

bp = Blueprint("r02", __name__)


@bp.route("/r02")
def r02():
    uid = request.args.get("id", "0")
    conn = sqlite3.connect(":memory:")
    return str(conn.execute("SELECT * FROM items WHERE id = ?", (uid,)).fetchall())
