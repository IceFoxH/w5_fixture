import sqlite3
from flask import Blueprint, request

bp = Blueprint("r09", __name__)


@bp.route("/r09")
def r09():
    uid = request.args.get("id", "0")
    conn = sqlite3.connect(":memory:")
    return str(conn.execute("SELECT * FROM items WHERE id = ?", (uid,)).fetchall())
