DROP TABLE IF EXISTS traders;
DROP TABLE IF EXISTS stocks;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS trades;

CREATE TABLE traders (
    traderid INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name CHAR(50) NOT NULL,
    last_name CHAR(50) NOT NULL,
    tradername CHAR(50) NOT NULL UNIQUE,
    hashword TEXT NOT NULL
);

CREATE TABLE stocks (
    stockid INTEGER PRIMARY KEY AUTOINCREMENT,
    stockname CHAR(50) NOT NULL,
    last_traded_price REAL,
    last_checked TEXT
);

CREATE TABLE orders (
    orderid INTEGER PRIMARY KEY AUTOINCREMENT,
    traderid INTEGER NOT NULL,
    stockid INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    selling INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (traderid) REFERENCES traders(traderid),
    FOREIGN KEY (stockid) REFERENCES stocks(stockid)
);

CREATE TABLE trades (
    tradeid INTEGER PRIMARY KEY AUTOINCREMENT,
    stockid INTEGER NOT NULL,
    sellerid INTEGER NOT NULL,
    buyerid INTEGER NOT NULL,
    trade_date TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (stockid) REFERENCES stocks(stockid),
    FOREIGN KEY (sellerid) REFERENCES traders(traderid),
    FOREIGN KEY (buyerid) REFERENCES traders(traderid)
);