import sqlite3

def save_history(user_id, movie_title, similarity):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, movie_title, similarity) VALUES (?, ?, ?)", (user_id, movie_title, similarity))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT movie_title, similarity, timestamp FROM history WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows