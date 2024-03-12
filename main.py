from flask import Flask, redirect, render_template, request, session, url_for, flash
from functools import wraps
from forms import RegistryForm, LoginForm, CreateOrderForm, ModifyOrderForm
import stockmarket as db
from tools import *

from flask_wtf.csrf import CSRFProtect
from datetime import datetime


app = Flask(__name__)
app.secret_key = '!secret'
csrf = CSRFProtect(app) # Add CSRF-protection (Cross-site request forgery) to the Flask-app.

db.reset_and_populate() # COMMENT OUT IF NOT MOCK POPULATING DATABASE!
db.start_scheduler() 

if __name__ == '__main__':
    """Boots the Flask-app environment.
    Configures the host, port and debug-mode.
    """
    app.run(host='127.0.0.1', port=8080, debug=False)


########## REST ROUTE FUNCTIONS ##########


def auth_required(f):
    """Decorator function for authenticating the users.
    Directs to login page in case not verified into session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'trader' not in session: # Checks if trader is in session.
            return redirect(url_for('login'))
        trader = session['trader']
        database_match = db.get_trader(trader['traderid'])
        if not database_match: # Checks that trader in session is in database.
            session.clear()
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
    tradername = form.tradername.data.strip()
    hashword = hash_password(form.password.data)
    db.add_trader(first_name, last_name, tradername, hashword)
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
    trader = db.get_trader_by_tradername(tradername)
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
    trader = session['trader']
    traderid = trader['traderid']
    owned_stock_offers = build_owned_stock_offers(traderid)
    owned_stock_bids = build_owned_stock_bids(traderid)
    return render_template('dashboard.html', trader=session['trader'], owned_stock_offers=owned_stock_offers, owned_stock_bids=owned_stock_bids)


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


@app.route('/trade_listing', methods=['GET'])
@auth_required
def trade_listing():
    """Lists all available trades.
    """
    trade_hierarchy = build_trade_hierarchy()
    return render_template('trade_listing.html', trade_hierarchy=trade_hierarchy)


@app.route('/order_create', methods=['GET'])
@auth_required
def order_create():
    """Creates a stock ordering form.
    """
    try:
        stockid = int(request.args.get('stockid'))
        order_type = request.args.get('order_type')
    except (TypeError, ValueError, AttributeError):
        flash("Could'n find the stock.", 'error')
        return redirect(url_for('dashboard'))
    stock = db.get_stock(stockid)
    form = CreateOrderForm()
    form.hidden.data = stockid
    form.type.data = order_type
    form.price.data = stock['last_traded_price']
    return render_template('order_create.html', form=form, stock=stock)
    

@app.route('/order_place', methods=['POST'])
@auth_required
def order_place():
    """Handles placing the stock order.
    """
    form = CreateOrderForm(request.form)
    stockid = int(form.hidden.data)
    stock = db.get_stock(stockid)
    if request.form.get("cancel", ""):
        return redirect(url_for('dashboard'))
    if not form.validate():
        return render_template('order_create.html', form=form, stock=stock)
    
    traderid = session['trader']['traderid']
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quantity = int(form.quantity.data)
    selling = form.type.data == 'Offer'
    price = float(form.price.data)
    orderid = db.add_order(traderid, stockid, order_date, quantity, selling, price)
    trade_made = run_order_matching(orderid)
    if trade_made:
        flash('Trade was made!', 'info')
    else:
        flash('New order was placed!', 'info')
    return redirect(url_for('dashboard'))


@app.route('/order_modify', methods=['GET'])
@auth_required
def order_modify():
    """Creates a stock modifying form.
    """
    try:
        stockid = int(request.args.get('stockid'))
        orderid = int(request.args.get('orderid'))
    except (TypeError, ValueError, AttributeError):
        flash("Could'n find the order.", 'error')
        redirect(url_for('dashboard'))
    stock = db.get_stock(stockid)
    order = db.get_order(orderid)
    form = ModifyOrderForm()
    form.hidden1.data = stockid
    form.hidden2.data = orderid
    form.type.data = 'Offer' if order['selling'] else 'Bid'
    form.price.data = order['price']
    form.quantity.data = order['quantity']
    return render_template('order_modify.html', form=form, stock=stock)
    

@app.route('/order_update', methods=['POST'])
@auth_required
def order_update():
    """Handles modifying the stock order.
    """
    form = ModifyOrderForm(request.form)
    stockid = int(form.hidden1.data)
    orderid = int(form.hidden2.data)
    stock = db.get_stock(stockid)
    if request.form.get("cancel", ""):
        return redirect(url_for('dashboard'))
    if request.form.get("delete", ""):
        db.delete_order(orderid)
        flash('Order was deleted!', 'info')
        return redirect(url_for("dashboard"))
    if not form.validate():
        return render_template('order_modify.html', form=form, stock=stock)
    
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quantity = int(form.quantity.data)
    selling = form.type.data == 'Offer'
    price = float(form.price.data)
    db.update_order(orderid, order_date, quantity, selling, price)
    trade_made = run_order_matching(orderid)
    if trade_made:
        flash('Trade was made!', 'info')
    else:
        flash('Order was modified!', 'info')
    return redirect(url_for('dashboard'))



########## SUPPORT FUNCTIONS ##########


def build_owned_stock_offers(traderid):
    """Builds a list of stocks along with their offers placed by the trader.
    """
    stocks = db.get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        offers = db.get_stock_offers_of_trader(stock['stockid'], traderid)
        if offers:
            stock['offers'] = offers
    filtered_stocks = [stock for stock in stocks if 'offers' in stock]
    return filtered_stocks


def build_owned_stock_bids(traderid):
    """Builds a list of stocks along with their bids placed by the trader.
    """
    stocks = db.get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        bids = db.get_stock_bids_of_trader(stock['stockid'], traderid)
        if not bids:
            continue
        if bids:
            stock['bids'] = bids
    filtered_stocks = [stock for stock in stocks if 'bids' in stock]
    return filtered_stocks


def build_offer_hierarchy():
    """Builds a hierarchy of all stocks and their respective offers
    and trader information.
    """
    stocks = db.get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        offers = db.get_stock_offers(stock['stockid'])
        if offers is None:
            offers = []
        if not offers:
            continue
        for offer in offers:
            traderid = offer.pop('traderid')
            offer['seller'] = db.get_trader_info(traderid)
        stock['offers'] = offers
    return stocks


def build_bid_hierarchy():
    """Builds a hierarchy of all stocks and their respective bids
    and trader information.
    """
    stocks = db.get_stocks()
    if not stocks:
        stocks = []
    for stock in stocks:
        bids = db.get_stock_bids(stock['stockid'])
        if bids is None:
            bids = []
        for bid in bids:
            traderid = bid.pop('traderid')
            bid['buyer'] = db.get_trader_info(traderid)
        stock['bids'] = bids
    return stocks


def build_trade_hierarchy():
    """Builds a hierarchy of all trades including detailed information
    about stocks, sellers, and buyers.
    """
    trades = db.get_trades()
    if not trades:
        trades = []
    for trade in trades:
        stock = db.get_stock(trade['stockid'])
        seller = db.get_trader(trade['sellerid'])
        buyer = db.get_trader(trade['buyerid'])
        trade['stockname'] = stock['stockname']
        trade['sellername'] = seller['tradername']
        trade['buyername'] = buyer['tradername']
    return trades


def run_order_matching(orderid):
    """Matches the given order with existing bids or offers creating trades
    and updating or removing the orders involved in the trades accordingly.
    """
    order = db.get_order(orderid)
    if order['selling']:
        sellerid = order['traderid']
        matching_orders = db.get_matching_bids(order['stockid'], order['traderid'], order['price'])
    else:
        buyerid = order['traderid']
        matching_orders = db.get_matching_offers(order['stockid'], order['traderid'], order['price'])
    
    if not matching_orders:
        return False

    for match in matching_orders:
        order = db.get_order(orderid)
        if order['selling']:
            buyerid = match['traderid']
        else:
            sellerid = match['traderid']
        trade_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        traded_price = max(order['price'], match['price'])
        traded_quantity = min(order['quantity'], match['quantity'])
        db.add_trade(order['stockid'], sellerid, buyerid, trade_date, traded_price, traded_quantity)
        match_new_quantity = match['quantity'] - traded_quantity
        order_new_quantity = order['quantity'] - traded_quantity
        if 0 < match_new_quantity:
            db.update_order(match['orderid'], match['order_date'], match_new_quantity, match['selling'], match['price'])
        else:
            db.delete_order(match['orderid'])
        if 0 < order_new_quantity:
            db.update_order(order['orderid'], order['order_date'], order_new_quantity, order['selling'], order['price'])
        else:
            db.delete_order(order['orderid'])
            break

    return matching_orders != None