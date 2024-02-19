DROP TABLE IF EXISTS trader;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS orders;

CREATE TABLE trader (
    traderid INTEGER PRIMARY KEY NOT NULL,
    tname CHAR(50) NOT NULL,
    hashword TEXT NOT NULL
);

CREATE TABLE stock (
    stockid INTEGER PRIMARY KEY NOT NULL,
    sname CHAR(50) NOT NULL,
    last_traded_price DECIMAL,
    last_checked DATETIME
);

CREATE TABLE orders (
    ordersid INTEGER PRIMARY KEY NOT NULL,
    traderid INTEGER NOT NULL,
    stockid INTEGER NOT NULL,
    odate DATETIME NOT NULL,
    quantity INTEGER NOT NULL,
    selling BOOLEAN NOT NULL,
    offer DECIMAL NOT NULL,
    CONSTRAINT orders_traderid
        FOREIGN KEY (traderid) 
        REFERENCES trader(traderid),
    CONSTRAINT orders_stockid
        FOREIGN KEY (stockid)
        REFERENCES stock(stockid)
);