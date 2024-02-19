import sqlite3
from datetime import datetime

date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO trader VALUES (?, ?, ?)",
            (1, 'John', '-'))

cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, 1, 1, date, 5, False, 182.31))

cur.execute("INSERT INTO stock VALUES (?, ?, ?, ?)",
            (1, 'Apple', 183.09, date))

connection.commit()
connection.close()