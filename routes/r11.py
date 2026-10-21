import sqlite3
from flask import Blueprint, request

bp = Blueprint("r11", __name__)


@bp.route("/r11")
def r11():
    uid = request.args.get("id", "0")
    conn = sqlite3.connect(":memory:")
    return str(conn.execute("SELECT * FROM items WHERE id = ?", (uid,)).fetchall())
