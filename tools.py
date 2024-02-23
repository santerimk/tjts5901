from passlib.hash import bcrypt
from datetime import datetime
import stockmarket as db



##### Password Tools #####


def verify_password(provided_password, hashword):
    """Verifies that the provided password matches with the stored
    bcrypt-hashed password.
    """
    verification_success = bcrypt.verify(provided_password, hashword)
    return verification_success


def hash_password(password):
    """Generates and returns a bcrypt hash of the provided password.
    """
    hashed_password = bcrypt.hash(password)
    return hashed_password



##### Jinja2 Tools #####


def build_owned_stock_offers(traderid):
    """Builds a list of stocks along with their offers placed by the trader.
    """
    stocks = get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        offers = get_stock_offers_of_trader(stock['stockid'], traderid)
        if offers:
            stock['offers'] = offers
    filtered_stocks = [stock for stock in stocks if 'offers' in stock]
    return filtered_stocks


def build_owned_stock_bids(traderid):
    """Builds a list of stocks along with their bids placed by the trader.
    """
    stocks = get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        bids = get_stock_bids_of_trader(stock['stockid'], traderid)
        if bids:
            stock['bids'] = bids
    filtered_stocks = [stock for stock in stocks if 'bids' in stock]
    return filtered_stocks


def build_offer_hierarchy():
    """Builds a hierarchy of all stocks and their respective offers
    and trader information.
    """
    stocks = get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        offers = get_stock_offers(stock['stockid'])
        for offer in offers:
            traderid = offer.pop('traderid')
            offer['seller'] = get_trader_info(traderid)
        stock['offers'] = offers
    return stocks


def build_bid_hierarchy():
    """Builds a hierarchy of all stocks and their respective bids
    and trader information.
    """
    stocks = get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        bids = get_stock_bids(stock['stockid'])
        for bid in bids:
            traderid = bid.pop('traderid')
            bid['buyer'] = get_trader_info(traderid)
        stock['bids'] = bids
    return stocks


def build_trade_hierarchy():
    """Builds a hierarchy of all trades including detailed information
    about stocks, sellers, and buyers.
    """
    trades = get_trades()
    if not trades:
        trades = []
    for trade in trades:
        stock = get_stock(trade['stockid'])
        seller = get_trader(trade['sellerid'])
        buyer = get_trader(trade['buyerid'])
        trade['stockname'] = stock['stockname']
        trade['sellername'] = seller['tradername']
        trade['buyername'] = buyer['tradername']
    return trades



##### Trade Tools #####


def run_order_matching(orderid):
    """Matches the given order with existing bids or offers creating trades
    and updating or removing the orders involved in the trades accordingly.
    """
    order = get_order(orderid)
    if order['selling']:
        sellerid = order['traderid']
        matching_orders = get_matching_bids(order['stockid'], order['traderid'], order['price'])
    else:
        buyerid = order['traderid']
        matching_orders = get_matching_offers(order['stockid'], order['traderid'], order['price'])

    for match in matching_orders:
        if order['selling']:
            buyerid = match['traderid']
        else:
            sellerid = match['traderid']
        trade_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        traded_price = max(order['price'], match['price'])
        traded_quantity = min(order['quantity'], match['quantity'])
        add_trade(order['stockid'], sellerid, buyerid, trade_date, traded_price, traded_quantity)
        match_new_quantity = match['quantity'] - traded_quantity
        order_new_quantity = order['quantity'] - traded_quantity
        if 0 < match_new_quantity:
            update_order(match['orderid'], match['order_date'], match_new_quantity, match['selling'], match['price'])
        else:
            delete_order(match['orderid'])
        if 0 < order_new_quantity:
            update_order(order['orderid'], order['order_date'], order_new_quantity, order['selling'], order['price'])
        else:
            delete_order(order['orderid'])
            break

    return matching_orders != None



##### Database Tools #####


def get_tradernames():
    """Retrieves a list of all tradernames of traders from the database.
    """
    trader_names = db.query("""
        SELECT tradername FROM traders
        """)
    return trader_names


def get_stocks():
    """Retrieves a list of all stocks from the database.
    """
    stocks = db.query("""
        SELECT * FROM stocks
        ORDER BY stockname ASC
        """)
    return stocks


def get_stock_bids(stockid):
    """Retrieves a list of all buy bids for a specific stock
    from the database.
    """
    bids = db.query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 0
        ORDER BY order_date DESC
        """, (stockid,))
    return bids


def get_stock_offers(stockid):
    """Retrieves a list of all sell offers for a specific stock
    from the database.
    """
    offers = db.query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 1
        ORDER BY order_date DESC
        """, (stockid,))
    return offers


def get_stock_bids_of_trader(stockid, traderid):
    """Retrieves a list of buy bids made by a specific trader
    for a specific stock from the database.
    """
    offers = db.query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 0 AND traderid = ?
        ORDER BY order_date DESC
        """, (stockid, traderid,))
    return offers


def get_stock_offers_of_trader(stockid, traderid):
    """Retrieves a list of sell offers made by a specific trader
    for a specific stock from the database.
    """
    offers = db.query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 1 AND traderid = ?
        ORDER BY order_date DESC
        """, (stockid, traderid,))
    return offers


def get_matching_bids(stockid, traderid, offering_price):
    """Retrieves bids for a stock that meet or exceed
    the specified offering price.
    """
    matching_bids = db.query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 0 AND price >= ? AND traderid != ?
        ORDER BY price DESC, order_date ASC
        """, (stockid, offering_price, traderid))
    return matching_bids


def get_matching_offers(stockid, traderid, bidding_price):
    """Retrieve offers for a stock that are at most equal to
    the specified bidding price.
    """
    matching_offers = db.query("""
        SELECT * FROM orders
        WHERE stockid = ? AND selling = 1 AND price <= ? AND traderid != ?
        ORDER BY price ASC, order_date ASC
        """, (stockid, bidding_price, traderid))
    return matching_offers


def get_trades():
    """Retrieve a list of all trades from the database.
    """
    trades = db.query("""
        SELECT * FROM trades
        ORDER BY trade_date ASC
        """)
    return trades


def get_trader(traderid):
    """Retrieves information about a trader from the database
    using their unique identifier.
    """
    trader = db.query("""
        SELECT traderid, first_name, last_name, tradername FROM traders
        WHERE traderid = ?
        """, (traderid,), True)
    return trader


def get_trader_info(traderid):
    """Retrieve basic information of a trader from the database
    using their unique identifier.
    """
    trader_info = db.query("""
        SELECT traderid, tradername FROM traders
        WHERE traderid = ?
        """, (traderid,), True)
    return trader_info


def get_trader_by_tradername(tradername):
    """Retrieves information about a trader from the database
    using their tradername.
    """
    trader = db.query("""
        SELECT traderid, first_name, last_name, tradername FROM traders
        WHERE tradername = ?
        """, (tradername,), True)
    return trader


def get_hashword_by_tradername(tradername):
    """Retrieves trader hashword from the database
    using their tradername.
    """
    trader = db.query("""
        SELECT hashword FROM traders
        WHERE tradername = ?
        """, (tradername,), True)
    return trader


def get_stock(stockid):
    """Retrieves information about a stock from the database
    using its unique identifier.
    """
    stock = db.query("""
        SELECT * FROM stocks
        WHERE stockid = ?
        """, (stockid,), True)
    return stock


def get_order(orderid):
    """Retrieves information about an order from the database
    using its unique identifier.
    """
    order = db.query("""
        SELECT * FROM orders
        WHERE orderid = ?
        """, (orderid,), True)
    return order


def add_trader(first_name, last_name, tradername, hashword):
    """Adds a new trader to the database.
    """
    traderid = db.modify("""
        INSERT INTO traders (first_name, last_name, tradername, hashword)
        VALUES (?, ?, ?, ?)
        """, (first_name, last_name, tradername, hashword))
    return traderid


def add_order(traderid, stockid, order_date, quantity, selling, price):
    """Adds a new order to the database.
    """
    orderid = db.modify("""
        INSERT INTO orders (traderid, stockid, order_date, quantity, selling, price)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (traderid, stockid, order_date, quantity, selling, price))
    return orderid


def add_trade(stockid, sellerid, buyerid, trade_date, price, quantity):
    """Adds a new trade to the database.
    """
    tradeid = db.modify("""
        INSERT INTO trades (stockid, sellerid, buyerid, trade_date, price, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (stockid, sellerid, buyerid, trade_date, price, quantity))
    return tradeid


def update_order(orderid, order_date, quantity, selling, price):
    """Updates information of an existing order in the database.
    """
    db.modify("""
        UPDATE orders
        SET order_date = ?, quantity = ?, selling = ?, price = ?
        WHERE orderid = ?
        """, (order_date, quantity, selling, price, orderid))


def delete_order(orderid):
    """Delete an order from the database.
    """
    db.modify("""
        DELETE FROM orders
        WHERE orderid = ?
        """, (orderid,))
