"""W5 fixture base: /a + /c 两个 SQLi。"""
import sqlite3

from flask import Flask, request

from routes.r01 import bp as r01
from routes.r02 import bp as r02
from routes.r03 import bp as r03
from routes.r04 import bp as r04
from routes.r05 import bp as r05
from routes.r06 import bp as r06
from routes.r07 import bp as r07
from routes.r08 import bp as r08
from routes.r09 import bp as r09
from routes.r10 import bp as r10
from routes.r11 import bp as r11
from routes.r12 import bp as r12

app = Flask(__name__)
    app.register_blueprint(r01)
    app.register_blueprint(r02)
    app.register_blueprint(r03)
    app.register_blueprint(r04)
    app.register_blueprint(r05)
    app.register_blueprint(r06)
    app.register_blueprint(r07)
    app.register_blueprint(r08)
    app.register_blueprint(r09)
    app.register_blueprint(r10)
    app.register_blueprint(r11)
    app.register_blueprint(r12)


@app.route("/a")
def a():
    uid = request.args.get("id", "")
    conn = sqlite3.connect(":memory:")
    return str(conn.execute("SELECT * FROM users WHERE id = " + uid).fetchall())


@app.route("/c")
def c():
    name = request.args.get("name", "")
    conn = sqlite3.connect(":memory:")
    return str(conn.execute("SELECT * FROM users WHERE name = '" + name + "'").fetchall())
