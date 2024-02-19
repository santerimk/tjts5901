import sqlite3
from flask import Flask

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/orders')
def orders():
    conn = get_db_connection()
    all_orders = 'SELECT * FROM orders'
    orders = conn.execute(all_orders).fetchall()
    conn.close()

    # Prints order results to console
    for order in orders:
        print(order[0])
        print(order[1])
        print(order[2])
        print(order[3])
        print(order[4])
        print(order[5])
        print(order[6])
    return ""