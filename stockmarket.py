import sqlite3
from datetime import datetime
from tools import hash_password

DATABASE_NAME = "stockmarket.db"


def get_connection():
    """For creating and returning database connections.
    """
    return sqlite3.connect(DATABASE_NAME)

def initialize():
    """For initializing the database.
    """
    conn = get_connection()
    with open('schema.sql', mode='r') as file:
        conn.executescript(file.read())
    conn.commit()
    conn.close()


# !!!USE ONLY IF YOU NEED TO RESET THE DATABASE TABLES AND REMOVE DATA!!!
def reset():
    """For resetting the database, dropping all tables and their data, recreating them."""
    conn = get_connection()
    with open('reset.sql', mode='r') as file:
        conn.executescript(file.read())
    conn.commit()
    conn.close()


def query(query, args=(), one=False):
    """For database queries, returning query results as rows.
    """
    initialize() # Makes sure database is initialized.
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
    initialize() # Makes sure database is initialized.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()
    conn.close()


def test_populate():
    # Insert traders
    traders_data = [
        ('Alex', 'Turner', 'alex_t', f'{hash_password("Pass123%")}'),
        ('Mia', 'Wallace', 'mia_w', f'{hash_password("Pass456%")}'),
        ('Ethan', 'Hunt', 'ethan_h', f'{hash_password("Pass789%")}')
    ]
    for trader in traders_data:
        modify("INSERT INTO traders (first_name, last_name, tradername, hashword) VALUES (?, ?, ?, ?)", trader)
        
    # Insert stocks
    stocks_data = [
        ('Amazon', 3300.00, '2023-02-01 12:00:00'),
        ('Apple', 145.45, '2023-02-01 13:00:00'),
        ('Facebook', 275.00, '2023-02-01 10:00:00'),
        ('Netflix', 510.50, '2023-02-01 11:00:00'),
        ('Tesla', 720.30, '2023-02-01 09:00:00')
    ]
    for stock in stocks_data:
        modify("INSERT INTO stocks (stockname, last_traded_price, last_checked) VALUES (?, ?, ?)", stock)
    
    # Insert orders
    orders_data = [
        (1, 1, '2023-02-02 09:00:00', 5, 1, 725.00),
        (2, 2, '2023-02-02 09:15:00', 10, 0, 270.00),
        (3, 3, '2023-02-02 09:30:00', 2, 1, 515.00),
        (1, 4, '2023-02-02 09:45:00', 1, 0, 3305.00),
        (2, 5, '2023-02-02 10:00:00', 8, 1, 140.00),
        (3, 1, '2023-02-02 10:15:00', 3, 0, 718.00),
        (1, 2, '2023-02-02 10:30:00', 7, 1, 280.00),
        (2, 3, '2023-02-02 10:45:00', 4, 0, 508.00),
        (3, 4, '2023-02-02 11:00:00', 1, 1, 3310.00),
        (1, 5, '2023-02-02 11:15:00', 5, 0, 147.00),
        (2, 1, '2023-02-02 11:30:00', 6, 1, 723.00),
        (3, 2, '2023-02-02 11:45:00', 9, 0, 277.00),
        (1, 3, '2023-02-02 12:00:00', 3, 1, 512.00),
        (2, 4, '2023-02-02 12:15:00', 2, 0, 3298.00),
        (3, 5, '2023-02-02 12:30:00', 7, 1, 146.00),
        (1, 1, '2023-02-02 12:45:00', 4, 0, 722.00),
        (2, 2, '2023-02-02 13:00:00', 10, 1, 276.00),
        (3, 3, '2023-02-02 13:15:00', 5, 0, 511.00),
        (1, 4, '2023-02-02 13:30:00', 1, 1, 3302.00),
        (2, 5, '2023-02-02 13:45:00', 8, 0, 143.50)
    ]
    for order in orders_data:
        modify("INSERT INTO orders (traderid, stockid, order_date, quantity, selling, price) VALUES (?, ?, ?, ?, ?, ?)", order)

