def safe_lookup(conn, uid):
    return conn.execute("SELECT * FROM items WHERE id = ?", (uid,)).fetchall()
