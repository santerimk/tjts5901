import sqlite3
from datetime import datetime

DATABASE_NAME = "stockmarket.db"

def initialize():
    """For initializing the database.
    """
    conn = get_connection()
    with open('schema.sql', mode='r') as file:
        conn.executescript(file.read())
    conn.commit()
    conn.close()


def get_connection():
    """For creating and returning database connections.
    """
    return sqlite3.connect(DATABASE_NAME)


def query(query, args=(), one=False):
    """For database queries, returning query results as rows.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    results = cur.fetchall()
    cur.close()
    conn.close()
    if not results:
        return None
    if one:
        return dict(results[0])
    return [dict(row) for row in results]


def modify(query, args=()):
    """For database functions of insert, update and delete.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()
    conn.close()


def test_populate():
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Insert a trader
    modify("INSERT INTO traders (first_name, last_name, tradername, hashword) VALUES (?, ?, ?, ?)",
        ('John', 'Snow', "JonnyBoi", "SOSLOLSX"))
    # Insert a stock
    modify("INSERT INTO stocks (stockname, last_traded_price, last_checked) VALUES (?, ?, ?)",
        ('Apple', 183.09, date))
    # Insert an order
    modify("INSERT INTO orders (traderid, stockid, order_date, quantity, selling, offer) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 1, date, 5, False, 182.31))
