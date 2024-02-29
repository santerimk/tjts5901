import sqlite3
from tools import *
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

DATABASE_NAME = "stockmarket.db"



########## SET UP TOOLS ##########


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
def reset_and_populate(): # TODO: Comment out once software complete.
    """For resetting the database, dropping all tables and their data,
    recreating them."""
    conn = get_connection()
    with open('reset.sql', mode='r') as file:
        conn.executescript(file.read())
    test_populate()
    conn.commit()
    conn.close()



########## GENERAL TOOLS ##########


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
    id = None
    if 'INSERT' in query:
        id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return id

# TODO: Implement the means to update stock "last_traded_price" and "last_checked" values hourly with AAPL.
def fetch_aapl_price():
    """Fetching the AAPL last traded price from the marketdata app API"""
    url = "https://api.marketdata.app/v1/stocks/quotes/AAPL/"
    try:
        response = requests.get(url)
        if response.status_code in [200, 203]:
            data = response.json()
            aapl_price = data.get('last', [None])[0]
            return aapl_price
        else:
            print(f"Failed to fetch AAPL price, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None


def update_aapl_stock_price(aapl_price):
    """
    Updating the AAPL stock price based on the API response. If API fetch fails,
    retains the old price.
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Fetch the current price from the database first
    current_price = query("""
        SELECT last_traded_price FROM stocks
        WHERE stockname = 'Apple'
        """, one=True)
    
    # If API fetch was successful, update with the new price; otherwise, skip update
    if aapl_price is not None:
        price_to_update = aapl_price
    else:
        print("API fetch failed, keeping the old price.")
        if current_price is not None:
            # Log current price or handle accordingly if needed
            print(f"Current price: {current_price['last_traded_price']}")
        return  # Exit function without updating price
    
    modify("""
        UPDATE stocks
        SET last_traded_price = ?, last_checked = ?
        WHERE stockname = 'Apple'
        """, (price_to_update, now))


def hourly_update():
    """ 
    Hourly update function with a scheduler in main.py
    """
    print("Executing hourly update..")
    price = fetch_aapl_price()
    update_aapl_stock_price(price)
    print(f"Updated AAPL stock price to {price} at {datetime.now()}")


def test_populate(): # TODO: Comment out once software complete.
    """For test populating the database with mock data,
    only for development purposes.
    """
    # Insert traders
    traders_data = [
        ('Alex', 'Turner', 'alex_t', f'{hash_password("Pass123%")}'),
        ('Mia', 'Wallace', 'mia_w', f'{hash_password("Pass456%")}'),
        ('Ethan', 'Hunt', 'ethan_h', f'{hash_password("Pass789%")}')
    ]
    for trader in traders_data:
        modify("""
            INSERT INTO traders (first_name, last_name, tradername, hashword)
            VALUES (?, ?, ?, ?)
            """, trader)
        
    # Insert stocks
    stocks_data = [
        ('Amazon', 3300.00, '2023-02-01 12:00:00'),
        ('Apple', 145.45, '2023-02-01 13:00:00'),
        ('Facebook', 275.00, '2023-02-01 10:00:00'),
        ('Netflix', 510.50, '2023-02-01 11:00:00'),
        ('Tesla', 720.30, '2023-02-01 09:00:00')
    ]
    for stock in stocks_data:
        modify("""
            INSERT INTO stocks (stockname, last_traded_price, last_checked)
            VALUES (?, ?, ?)
            """, stock)
    
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
        modify("""
            INSERT INTO orders (traderid, stockid, order_date, quantity, selling, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """, order)
        


########## SPECIFIC TOOLS ##########


def get_tradernames():
    """Retrieves a list of all tradernames of traders from the database.
    """
    trader_names = query("""
        SELECT tradername FROM traders
        """)
    return trader_names


def get_stocks():
    """Retrieves a list of all stocks from the database.
    """
    stocks = query("""
        SELECT * FROM stocks
        ORDER BY stockname ASC
        """)
    return stocks


def get_stock_bids(stockid):
    """Retrieves a list of all buy bids for a specific stock
    from the database.
    """
    bids = query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 0
        ORDER BY order_date DESC
        """, (stockid,))
    return bids


def get_stock_offers(stockid):
    """Retrieves a list of all sell offers for a specific stock
    from the database.
    """
    offers = query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 1
        ORDER BY order_date DESC
        """, (stockid,))
    return offers


def get_stock_bids_of_trader(stockid, traderid):
    """Retrieves a list of buy bids made by a specific trader
    for a specific stock from the database.
    """
    offers = query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 0 AND traderid = ?
        ORDER BY order_date DESC
        """, (stockid, traderid,))
    return offers


def get_stock_offers_of_trader(stockid, traderid):
    """Retrieves a list of sell offers made by a specific trader
    for a specific stock from the database.
    """
    offers = query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 1 AND traderid = ?
        ORDER BY order_date DESC
        """, (stockid, traderid,))
    return offers


def get_matching_bids(stockid, traderid, offering_price):
    """Retrieves bids for a stock that meet or exceed
    the specified offering price.
    """
    matching_bids = query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 0 AND price >= ? AND traderid != ?
        ORDER BY price DESC, order_date ASC
        """, (stockid, offering_price, traderid))
    return matching_bids


def get_matching_offers(stockid, traderid, bidding_price):
    """Retrieve offers for a stock that are at most equal to
    the specified bidding price.
    """
    matching_offers = query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 1 AND price <= ? AND traderid != ?
        ORDER BY price ASC, order_date ASC
        """, (stockid, bidding_price, traderid))
    return matching_offers


def get_trades():
    """Retrieve a list of all trades from the database.
    """
    trades = query("""
        SELECT * FROM trades
        ORDER BY trade_date ASC
        """)
    return trades


def get_trader(traderid):
    """Retrieves information about a trader from the database
    using their unique identifier.
    """
    trader = query("""
        SELECT traderid, first_name, last_name, tradername FROM traders
        WHERE traderid = ?
        """, (traderid,), True)
    return trader


def get_trader_info(traderid):
    """Retrieve basic information of a trader from the database
    using their unique identifier.
    """
    trader_info = query("""
        SELECT traderid, tradername FROM traders
        WHERE traderid = ?
        """, (traderid,), True)
    return trader_info


def get_trader_by_tradername(tradername):
    """Retrieves information about a trader from the database
    using their tradername.
    """
    trader = query("""
        SELECT traderid, first_name, last_name, tradername FROM traders
        WHERE tradername = ?
        """, (tradername,), True)
    return trader


def get_hashword_by_tradername(tradername):
    """Retrieves trader hashword from the database
    using their tradername.
    """
    trader = query("""
        SELECT hashword FROM traders
        WHERE tradername = ?
        """, (tradername,), True)
    return trader


def get_stock(stockid):
    """Retrieves information about a stock from the database
    using its unique identifier.
    """
    stock = query("""
        SELECT * FROM stocks
        WHERE stockid = ?
        """, (stockid,), True)
    return stock


def get_order(orderid):
    """Retrieves information about an order from the database
    using its unique identifier.
    """
    order = query("""
        SELECT * FROM orders
        WHERE orderid = ?
        """, (orderid,), True)
    return order


def add_trader(first_name, last_name, tradername, hashword):
    """Adds a new trader to the database.
    """
    traderid = modify("""
        INSERT INTO traders (first_name, last_name, tradername, hashword)
        VALUES (?, ?, ?, ?)
        """, (first_name, last_name, tradername, hashword))
    return traderid


def add_order(traderid, stockid, order_date, quantity, selling, price):
    """Adds a new order to the database.
    """
    orderid = modify("""
        INSERT INTO orders (traderid, stockid, order_date, quantity, selling, price)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (traderid, stockid, order_date, quantity, selling, price))
    return orderid


def add_trade(stockid, sellerid, buyerid, trade_date, price, quantity):
    """Adds a new trade to the database.
    """
    tradeid = modify("""
        INSERT INTO trades (stockid, sellerid, buyerid, trade_date, price, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (stockid, sellerid, buyerid, trade_date, price, quantity))
    return tradeid


def update_order(orderid, order_date, quantity, selling, price):
    """Updates information of an existing order in the database.
    """
    modify("""
        UPDATE orders
        SET order_date = ?, quantity = ?, selling = ?, price = ?
        WHERE orderid = ?
        """, (order_date, quantity, selling, price, orderid))


def delete_order(orderid):
    """Delete an order from the database.
    """
    modify("""
        DELETE FROM orders
        WHERE orderid = ?
        """, (orderid,))


