from flask import Flask, redirect, render_template, request, session, url_for, flash
from functools import wraps
from forms import RegistryForm, LoginForm, StockOrderForm
import stockmarket as db
from tools import hash_password
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

app = Flask(__name__)
app.secret_key = '!secret'
csrf = CSRFProtect(app) # Add CSRF-protection (Cross-site request forgery) to the Flask-app.

db.reset() # TODO: Remove once done with testing the database.
db.test_populate() # TODO: Remove once done with testing the database.

if __name__ == '__main__':
    """Boots in a Flask-app environment.
    Defines the host, port and debug-mode for the app.
    """
    app.run(host='127.0.0.1', port=8080, debug=True)


def auth_required(f):
    """Decorator function for authenticating the users.
    Directs to login page in case not verified into session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'trader' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Redirects the user to the front page.
    """
    return redirect(url_for('dashboard'))


@app.route('/registry', methods=['GET'])
def registry():
    """Creates a trader registry page.
    """
    form = RegistryForm()
    return render_template('registry.html', form=form)


@app.route('/register', methods=['POST'])
def register():
    """Handles the registering of the trader.
    """
    form = RegistryForm(request.form)
    if request.form.get("cancel", ""):
        return redirect(url_for('login'))
    if not form.validate():
        return render_template('registry.html', form=form)
    first_name = form.first_name.data.strip().lower().capitalize()
    last_name = form.last_name.data.strip().lower().capitalize()
    tradername = form.tradername.data.strip() # TODO: Decide whether the tradername should be caseinsensitive or not.
    hashword = hash_password(form.password.data)
    add_trader(first_name, last_name, tradername, hashword)
    flash(f'New trader "{tradername}" registered!', 'info')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET'])
def login():
    """Creates a trader login page.
    """
    form = LoginForm()
    return render_template('login.html', form=form)
    

@app.route('/auth', methods=['POST'])
def auth():
    """Handles the authentication of the login.
    """
    form = LoginForm(request.form)
    if not form.validate():
        return render_template('login.html', form=form)
    tradername = form.tradername.data.strip()
    trader = get_trader(tradername)
    session['trader'] = trader
    return redirect(url_for('dashboard'))


@app.route('/logout', methods=['GET'])
def logout():
    """Clears the session, logging the user out.
    """
    session.clear()
    return redirect('/')


@app.route('/dashboard', methods=['GET'])
@auth_required
def dashboard():
    """Shows the trader dashboard.
    """
    return render_template('dashboard.html', trader=session['trader'])


@app.route('/stock_listing', methods=['GET'])
@auth_required
def stock_listing():
    """Lists all available stocks.
    """
    stocks = get_stocks()
    return render_template('stock_listing.html', stocks=stocks)


@app.route('/offer_listing', methods=['GET'])
@auth_required
def offer_listing():
    """Lists all available offers.
    """
    offer_hierarchy = build_offer_hierarchy()
    return render_template('offer_listing.html', offer_hierarchy=offer_hierarchy)


@app.route('/bid_listing', methods=['GET'])
@auth_required
def bid_listing():
    """Lists all available bids.
    """
    bid_hierarchy = build_bid_hierarchy()
    return render_template('bid_listing.html', bid_hierarchy=bid_hierarchy)


@app.route('/order_create', methods=['GET'])
def order_create():
    """Creates a stock ordering form.
    """
    try:
        stockid = int(request.args.get('stockid'))
    except AttributeError:
        flash("Could'n find the stock.", 'error')
        redirect(url_for('dashboard'))
    stock = get_stock(stockid)
    form = StockOrderForm()
    form.hidden.data = stockid
    return render_template('order_create.html', form=form, stock=stock)
    

@app.route('/order_place', methods=['POST'])
def order_place():
    """Handles placing the stock order.
    """
    form = StockOrderForm(request.form)
    stockid = int(form.hidden.data)
    stock = get_stock(stockid)
    if request.form.get("cancel", ""):
        return redirect(url_for('stock_listing'))
    if not form.validate():
        return render_template('order_create.html', form=form, stock=stock)
    
    traderid = session['trader']['traderid']
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quantity = int(form.quantity.data)
    selling = form.type.data == 'Offer'
    price = float(form.price.data)
    add_order(traderid, stockid, order_date, quantity, selling, price)
    flash('New order placed!', 'info')
    # TODO: Add the logic of checking and possibly completing transactions between matching bids and offers.
    return redirect(url_for('dashboard'))


@app.route('/orders', methods=['GET'])
@auth_required
def orders():
    orders_query = 'SELECT * FROM orders'
    orders = db.query(orders_query)
    for order in orders: # Prints order results to console
        print(order['id'])
        print(order['trader_id'])
        print(order['stock_id'])
        print(order['date'])
        print(order['quantity'])
        print(order['is_buy'])
        print(order['price'])
    return "Orders printed!"


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


def get_stock_offers(stockid):
    """Fetch orders where `selling` is 1 for the current stock
    """
    offers = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 1 ORDER BY order_date DESC", (stockid,))
    return offers


def get_stock_bids(stockid):
    """Fetch orders where `selling` is 1 for the current stock
    """
    bids = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 0 ORDER BY order_date DESC", (stockid,))
    return bids


def get_trader_info(traderid):
    trader_info = db.query("SELECT traderid, tradername FROM traders WHERE traderid = ?", (traderid,), True)
    return trader_info