import sqlite3
from unittest.util import _MAX_LENGTH
from models import Complaint

conn = sqlite3.connect('social.db')
cursor = conn.cursor()

def create():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Social (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT 
            Text TEXT NOT NULL
        )''')
    conn.commit()


def add(text, name):
    cursor.execute('''
        INSERT INTO Social (Name, Text)
        VALUES (?, ?)''', (text, name))
    conn.commit()