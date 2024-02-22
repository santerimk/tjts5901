from passlib.hash import bcrypt
import stockmarket as db


def verify_password(provided_password, hashword):
    """Verifies that the trader password matches with the stored hash.
    """
    verification_success = bcrypt.verify(provided_password, hashword)
    return verification_success


def hash_password(password):
    """Generates and returns a bcrypt-hash of the password.
    """
    hashed_password = bcrypt.hash(password)
    return hashed_password


def build_owned_stock_offers(traderid):
    stocks = get_stocks()
    for stock in stocks:
        offers = get_stock_offers_of_trader(stock['stockid'], traderid)
        if offers:
            stock['offers'] = offers
    filtered_stocks = [stock for stock in stocks if 'offers' in stock]
    return filtered_stocks


def build_owned_stock_bids(traderid):
    stocks = get_stocks()
    for stock in stocks:
        bids = get_stock_bids_of_trader(stock['stockid'], traderid)
        if bids:
            stock['bids'] = bids
    filtered_stocks = [stock for stock in stocks if 'bids' in stock]
    return filtered_stocks


def build_offer_hierarchy():
    stocks = get_stocks()
    for stock in stocks:
        offers = get_stock_offers(stock['stockid'])
        for offer in offers:
            traderid = offer.pop('traderid')
            offer['seller'] = get_trader_info(traderid)
        stock['offers'] = offers
    return stocks


def build_bid_hierarchy():
    stocks = get_stocks()
    for stock in stocks:
        bids = get_stock_bids(stock['stockid'])
        for bid in bids:
            traderid = bid.pop('traderid')
            bid['buyer'] = get_trader_info(traderid)
        stock['bids'] = bids
    return stocks


def get_trader(tradername):
    trader = db.query("SELECT traderid, first_name, last_name, tradername FROM traders WHERE tradername = ?", (tradername,), True)
    return trader


def add_trader(first_name, last_name, tradername, hashword):
    db.modify("INSERT INTO traders (first_name, last_name, tradername, hashword) VALUES (?, ?, ?, ?)", (first_name, last_name, tradername, hashword))


def add_order(traderid, stockid, order_date, quantity, selling, price):
    db.modify("INSERT INTO orders (traderid, stockid, order_date, quantity, selling, price) VALUES (?, ?, ?, ?, ?, ?)", (traderid, stockid, order_date, quantity, selling, price))


def get_stocks():
    stocks_query = "SELECT * FROM stocks ORDER BY stockname ASC"
    stocks = db.query(stocks_query)
    return stocks


def get_stock(stockid):
    stock = db.query("SELECT * FROM stocks WHERE stockid = ?", (stockid,), True)
    return stock


def get_order(orderid):
    order = db.query("SELECT * FROM orders WHERE orderid = ?", (orderid,), True)
    return order


def update_order(orderid, order_date, quantity, selling, price):
    db.modify("""
        UPDATE orders
        SET order_date = ?, quantity = ?, selling = ?, price = ?
        WHERE orderid = ?
        """, (order_date, quantity, selling, price, orderid))


def delete_order(orderid):
    db.modify("DELETE FROM orders WHERE orderid = ?", (orderid,))


def get_stock_offers(stockid):
    offers = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 1 ORDER BY order_date DESC", (stockid,))
    return offers


def get_stock_offers_of_trader(stockid, traderid):
    offers = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 1 AND traderid = ? ORDER BY order_date DESC", (stockid, traderid,))
    return offers


def get_stock_bids(stockid):
    bids = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 0 ORDER BY order_date DESC", (stockid,))
    return bids


def get_stock_bids_of_trader(stockid, traderid):
    offers = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 0 AND traderid = ? ORDER BY order_date DESC", (stockid, traderid,))
    return offers


def get_trader_info(traderid):
    trader_info = db.query("SELECT traderid, tradername FROM traders WHERE traderid = ?", (traderid,), True)
    return trader_info