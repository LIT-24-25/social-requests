import sqlite3

conn = sqlite3.connect('social.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Social (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Text TEXT NOT NULL
    )''')
conn.commit()

def add(text):
    cursor.execute('''
        INSERT INTO Social (Text)
        VALUES (?)''', (text,))
    conn.commit()