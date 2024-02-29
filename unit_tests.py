import unittest
from unittest.mock import patch, MagicMock, ANY
import stockmarket
from stockmarket import add_trader, fetch_aapl_price, update_aapl_stock_price, hourly_update, get_tradernames, get_stocks, get_stock_bids, get_stock_offers, get_stock_bids_of_trader, get_stock_offers_of_trader, get_matching_bids, get_matching_offers, get_trades, get_trader, get_trader_info, get_trader_by_tradername, get_hashword_by_tradername, get_stock, get_order, add_order, add_trade, update_order, delete_order, requests
from datetime import datetime

def add(a, b):
    """add"""
    return a + b

def subtract(a, b):
    """subs"""
    return a - b


def multiply(a, b):
    """mult"""
    return a * b


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(-1, -1) == -2

def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(-1, -1) == 0
    assert subtract(5, 2) == 3


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-1, 1) == -1
    assert multiply(-1, -1) == 1


class TestStockMarketFunctions(unittest.TestCase):

    def setUp(self):
        # Patch 'sqlite3.connect' and 'requests.get' before each test
        self.mock_connect = patch('stockmarket.sqlite3.connect').start()
        self.mock_get = patch('stockmarket.requests.get').start()
        
        # Setup mock database connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.lastrowid = 1  # Default mock for the inserted row ID
        
        # Default setup for mock response for requests.get
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {'last': [123.45]}
        self.mock_get.return_value = self.mock_response


    def tearDown(self):
        # Stop all patches after each test
        patch.stopall()


    def test_add_trader(self):
        """ testing for add_trader function
        """
        # Call the function
        trader_id = add_trader('John', 'Doe', 'johndoe', 'hashedpassword')
        # Assertions
        self.assertEqual(trader_id, 1)

    def test_hourly_update(self):
        """ Test for the hourly update function
        """
        hourly_update()

        # Since modify is a local function, we need to patch it within the context of this test
        with patch('stockmarket.modify') as mock_modify:
            mock_modify.return_value = None
            # Set up fetch_aapl_price to return a specific price
            self.mock_response.json.return_value = {'last': [123.45]}
            hourly_update()
            # Assertions
            mock_modify.assert_called_once_with(ANY, (123.45, unittest.mock.ANY))


    @patch('stockmarket.get_connection')
    def test_query_multiple_rows(self, mock_get_connection):
        """ Test for query function multiple rows using MagicMock
        """
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Adjust mock cursor's fetchall to return sample data as dictionaries
        # This simulates the behavior of fetchall() when conn.row_factory = sqlite3.Row
        mock_data = [{'name': 'Alice', 'id': 1}, {'name': 'Bob', 'id': 2}]
        mock_cursor.fetchall.return_value = mock_data
        
        # Call the function under test
        sql = "SELECT name, id FROM users"
        result = stockmarket.query(sql)
        
        # Verify SQL execution
        mock_cursor.execute.assert_called_once_with(sql, ())
        
        # Check return value structure
        expected_result = [{'name': 'Alice', 'id': 1}, {'name': 'Bob', 'id': 2}]
        self.assertEqual(result, expected_result)

    @patch('stockmarket.get_connection')
    def test_query_single_row(self, mock_get_connection):
        """ Test for query function single rows using MagicMock
        """
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Directly mock cursor's fetchall to return a list of dictionaries
        # This simulates the behavior of fetchall() when conn.row_factory = sqlite3.Row
        mock_data = [{'name': 'Alice', 'id': 1}]
        mock_cursor.fetchall.return_value = mock_data

        # Call the function with 'one=True'
        sql = "SELECT name, id FROM users WHERE name = ?"
        result = stockmarket.query(sql, args=('Alice',), one=True)

        # Verify SQL execution
        mock_cursor.execute.assert_called_once_with(sql, ('Alice',))

        # Check return value structure
        expected_result = {'name': 'Alice', 'id': 1}
        self.assertEqual(result, expected_result)

    @patch('stockmarket.get_connection')
    def test_modify_insert(self, mock_get_connection):
        """ Test for modify insert
        """
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1 

        # Example SQL insert query
        sql = "INSERT INTO users (name, age) VALUES (?, ?)"
        args = ('Alice', 30)

        # Call the function under test
        row_id = stockmarket.modify(sql, args)

        # Verify SQL execution
        mock_cursor.execute.assert_called_with(sql, args)
        mock_conn.commit.assert_called()

        self.assertEqual(row_id, 1)

    @patch('stockmarket.get_connection')
    def test_modify_update(self, mock_get_connection):
        """ Test for modify update
        """
        # Setup for an update operation is similar to insert, without the lastrowid
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Example SQL update query
        sql = "UPDATE users SET age = ? WHERE name = ?"
        args = (35, 'Alice')

        # Call the function under test
        result = stockmarket.modify(sql, args)

        # Verify SQL execution
        mock_cursor.execute.assert_called_with(sql, args)
        mock_conn.commit.assert_called()
        
        self.assertIsNone(result)

class TestFetchAPI(unittest.TestCase):
        
    @patch('stockmarket.requests.get')
    def test_fetch_success(self, mock_get):
        """ Test for the success of fetch
        """
        # Mock a successful API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'last': [150.00]}

        price = fetch_aapl_price()
        self.assertEqual(price, 150.00)

    @patch('stockmarket.requests.get')
    def test_fetch_failure(self, mock_get):
        """ Test for the failure of fetch
        """
        # Mock a failure in API response
        mock_get.return_value.status_code = 404

        price = fetch_aapl_price()
        self.assertIsNone(price)

    @patch('stockmarket.modify')
    @patch('stockmarket.query')
    @patch('stockmarket.datetime')
    def test_update_stock_price(self, mock_datetime, mock_query, mock_modify):
        """ Test for the update of stock price
        """
        # Setup the mock for datetime.now() to return a specific datetime
        mock_datetime.now.return_value.strftime.return_value = '2024-02-29 15:31:23'
        mock_query.return_value = {'last_traded_price': 100.00}  # Simulate existing price
        new_price = 150.00  # Simulate new fetched price

        # Call the function
        update_aapl_stock_price(new_price)

        # Normalize SQL query string for comparison
        actual_call_args = mock_modify.call_args[0]
        actual_sql = " ".join(actual_call_args[0].split())
        actual_params = actual_call_args[1]

        expected_sql = "UPDATE stocks SET last_traded_price = ?, last_checked = ? WHERE stockname = 'Apple'"
        expected_params = (150.0, '2024-02-29 15:31:23')

        # Assert modify was called with normalized SQL query and correct parameters
        self.assertEqual(actual_sql, expected_sql)
        self.assertEqual(actual_params, expected_params)

    @patch('stockmarket.modify')
    @patch('stockmarket.query')
    @patch('stockmarket.datetime')
    def test_update_fetch_failure(self, mock_datetime, mock_query, mock_modify):
        """ Test for failure of the update fetch with modify
        """
        # Set up mocks
        mock_datetime.return_value.strftime.return_value = '2024-02-29 15:31:23'
        mock_query.return_value = {'last_traded_price': 100.00}  # Simulate existing price
        
        # Call the function with None to simulate fetch failure
        update_aapl_stock_price(None)

        # Assert modify was NOT called, since update should be skipped
        mock_modify.assert_not_called()

class TestSpecificTools(unittest.TestCase):
    @patch('stockmarket.query')
    def test_get_tradernames(self, mock_query):
        """ Test for getting tradernames
        """  
        # Mock return value of query to simulate database response
        mock_query.return_value = [{'tradername': 'Alice'}, {'tradername': 'Bob'}]
        result = get_tradernames()

        # Normalize the expected SQL query by removing leading/trailing whitespaces and newlines
        expected_sql = "SELECT tradername FROM traders"
        actual_sql = " ".join(mock_query.call_args[0][0].split())

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(result, [{'tradername': 'Alice'}, {'tradername': 'Bob'}])

    

    @patch('stockmarket.query')
    def test_get_stocks(self, mock_query):
        """ Test for getting stocks
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = [
            {'stockname': 'Apple', 'last_traded_price': 150.00, 'last_checked': '2024-02-29'},
            {'stockname': 'Microsoft', 'last_traded_price': 250.00, 'last_checked': '2024-02-29'}
        ]
        result = get_stocks()

        # Normalize the SQL query strings for comparison
        expected_sql = 'SELECT * FROM stocks ORDER BY stockname ASC'
        actual_sql = mock_query.call_args[0][0].replace('\n', ' ').strip()

        # Compare the normalized expected and actual SQL
        self.assertEqual(' '.join(expected_sql.split()), ' '.join(actual_sql.split()))

        # Asserts
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['stockname'], 'Apple')


    @patch('stockmarket.query')
    def test_get_stock_bids(self, mock_query):
        """ Test for getting stock bids
        """  
        # Setup the mock to return a simulated database response for bids
        mock_query.return_value = [
            {'order_id': 1, 'stockid': 1, 'selling': 0, 'order_date': '2024-02-29', 'quantity': 100, 'price': 150.00},
            {'order_id': 2, 'stockid': 1, 'selling': 0, 'order_date': '2024-02-28', 'quantity': 50, 'price': 145.00}
        ]
        stock_id = 1
        result = get_stock_bids(stock_id)

        # Normalize the SQL query strings for comparison
        expected_sql = 'SELECT * FROM orders WHERE stockid = ? AND selling = 0 ORDER BY order_date DESC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_stock_offers(self, mock_query):
        """ Test for getting stock offers
        """  
        # Setup the mock to return a simulated database response for offers
        mock_query.return_value = [
            {'order_id': 3, 'stockid': 1, 'selling': 1, 'order_date': '2024-02-27', 'quantity': 200, 'price': 155.00},
            {'order_id': 4, 'stockid': 1, 'selling': 1, 'order_date': '2024-02-26', 'quantity': 100, 'price': 152.00}
        ]
        stock_id = 1 
        result = get_stock_offers(stock_id)

        # Normalize the SQL query strings for comparison
        expected_sql = 'SELECT * FROM orders WHERE stockid = ? AND selling = 1 ORDER BY order_date DESC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_stock_bids_of_trader(self, mock_query):
        """ Test for getting stock bids of a specific trader
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = [
            {'order_id': 1, 'stockid': 1, 'traderid': 1, 'selling': 0, 'order_date': '2024-02-29', 'quantity': 100, 'price': 150.00}
        ]
        stock_id = 1
        trader_id = 1
        result = get_stock_bids_of_trader(stock_id, trader_id)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT * FROM orders WHERE stockid = ? AND selling = 0 AND traderid = ? ORDER BY order_date DESC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id, trader_id))
        self.assertEqual(result, mock_query.return_value)
    

    @patch('stockmarket.query')
    def test_get_stock_offers_of_trader(self, mock_query):
        """ Test for getting stock offers of a specific trader
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = [
            {'order_id': 2, 'stockid': 1, 'traderid': 1, 'selling': 1, 'order_date': '2024-02-28', 'quantity': 50, 'price': 155.00}
        ]
        stock_id = 1
        trader_id = 1
        result = get_stock_offers_of_trader(stock_id, trader_id)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT * FROM orders WHERE stockid = ? AND selling = 1 AND traderid = ? ORDER BY order_date DESC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id, trader_id))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_matching_bids(self, mock_query):
        """ Test for getting matching bids
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = [
            {'order_id': 3, 'stockid': 1, 'traderid': 2, 'selling': 0, 'order_date': '2024-02-27', 'quantity': 200, 'price': 160.00}
        ]
        stock_id = 1
        trader_id = 1
        offering_price = 155.00

        result = get_matching_bids(stock_id, trader_id, offering_price)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT * FROM orders WHERE stockid = ? AND selling = 0 AND price >= ? AND traderid != ? ORDER BY price DESC, order_date ASC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id, offering_price, trader_id))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_matching_offers(self, mock_query):
        """ Test for getting matching orders
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = [
            {'order_id': 4, 'stockid': 1, 'traderid': 2, 'selling': 1, 'order_date': '2024-02-26', 'quantity': 100, 'price': 150.00}
        ]
        stock_id = 1
        trader_id = 1
        bidding_price = 155.00

        result = get_matching_offers(stock_id, trader_id, bidding_price)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT * FROM orders WHERE stockid = ? AND selling = 1 AND price <= ? AND traderid != ? ORDER BY price ASC, order_date ASC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]
        
        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id, bidding_price, trader_id))
        self.assertEqual(result, mock_query.return_value) 


    @patch('stockmarket.query')
    def test_get_trades(self, mock_query):
        """ Test for getting trades by trade id
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = [
            {'trade_id': 1, 'trade_date': '2024-02-29', 'stockid': 1, 'price': 150.00, 'quantity': 100},
            {'trade_id': 2, 'trade_date': '2024-02-28', 'stockid': 2, 'price': 250.00, 'quantity': 50}
        ]
        result = get_trades()

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT * FROM trades ORDER BY trade_date ASC'
        actual_sql = " ".join(mock_query.call_args[0][0].split())

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_trader(self, mock_query):
        """ Test for getting a trader
        """
        # Setup the mock to return a simulated database response
        mock_query.return_value = {
            'traderid': 1, 'first_name': 'John', 'last_name': 'Doe', 'tradername': 'johndoe'
        }
        trader_id = 1
        result = get_trader(trader_id)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT traderid, first_name, last_name, tradername FROM traders WHERE traderid = ?'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (trader_id,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_trader_info(self, mock_query):
        """ Test for getting a trader's info
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = {'traderid': 1, 'tradername': 'john_doe'}
        trader_id = 1

        result = get_trader_info(trader_id)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT traderid, tradername FROM traders WHERE traderid = ?'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (trader_id,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_trader_by_tradername(self, mock_query):
        """ Test for getting a trader by trader's name
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = {'traderid': 1, 'first_name': 'John', 'last_name': 'Doe', 'tradername': 'john_doe'}
        tradername = 'john_doe'

        result = get_trader_by_tradername(tradername)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT traderid, first_name, last_name, tradername FROM traders WHERE tradername = ?'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (tradername,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_hashword_by_tradername(self, mock_query):
        """ Test for getting the hashword for individual trader by name
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = {'hashword': 'hashed_password'}
        tradername = 'john_doe'

        result = get_hashword_by_tradername(tradername)

        # Expected and actual SQL query normalization and comparison
        expected_sql = 'SELECT hashword FROM traders WHERE tradername = ?'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (tradername,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_stock(self, mock_query):
        """ Test for getting a stock
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = {
            'stockid': 1, 'stockname': 'Apple', 'last_traded_price': 150.00, 'last_checked': '2024-02-29'
        }
        stock_id = 1
        result = get_stock(stock_id)

        # Normalize the SQL query strings for comparison
        expected_sql = 'SELECT * FROM stocks WHERE stockid = ?'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stock_id,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.query')
    def test_get_order(self, mock_query):
        """ Test for getting an order
        """  
        # Setup the mock to return a simulated database response
        mock_query.return_value = {
            'orderid': 1, 'traderid': 1, 'stockid': 1, 'order_date': '2024-02-29', 'quantity': 100, 'price': 150.00, 'selling': 0
        }
        order_id = 1
        result = get_order(order_id)

        # Normalize the SQL query strings for comparison
        expected_sql = 'SELECT * FROM orders WHERE orderid = ?'
        actual_sql = " ".join(mock_query.call_args[0][0].split())
        actual_params = mock_query.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (order_id,))
        self.assertEqual(result, mock_query.return_value)


    @patch('stockmarket.modify')
    def test_add_trader(self, mock_modify):
        """ Test for adding a trader
        """  
        first_name = 'John'
        last_name = 'Doe'
        tradername = 'johndoe'
        hashword = 'hashedpassword'
        mock_modify.return_value = 1

        trader_id = add_trader(first_name, last_name, tradername, hashword)

        # Normalize the SQL query strings for comparison
        expected_sql = " ".join("""
            INSERT INTO traders (first_name, last_name, tradername, hashword)
            VALUES (?, ?, ?, ?)
            """.split())
        actual_sql = " ".join(mock_modify.call_args[0][0].split())
        actual_params = mock_modify.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (first_name, last_name, tradername, hashword))
        self.assertEqual(trader_id, mock_modify.return_value)


    @patch('stockmarket.modify')
    def test_add_order(self, mock_modify):
        """ Test for adding an order
        """  
        traderid = 1
        stockid = 1
        order_date = '2024-02-29'
        quantity = 100
        selling = 0
        price = 150.00
        mock_modify.return_value = 1

        order_id = add_order(traderid, stockid, order_date, quantity, selling, price)

        # Normalize the SQL query strings for comparison
        expected_sql = " ".join("""
            INSERT INTO orders (traderid, stockid, order_date, quantity, selling, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """.split())
        actual_sql = " ".join(mock_modify.call_args[0][0].split())
        actual_params = mock_modify.call_args[0][1]

        #Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (traderid, stockid, order_date, quantity, selling, price))
        self.assertEqual(order_id, mock_modify.return_value)


    @patch('stockmarket.modify')
    def test_add_trade(self, mock_modify):
        """ Test for adding a trade
        """        
        stockid = 1
        sellerid = 1
        buyerid = 2
        trade_date = '2024-02-29'
        price = 150.00
        quantity = 100
        mock_modify.return_value = 1

        trade_id = add_trade(stockid, sellerid, buyerid, trade_date, price, quantity)

        # Normalize the SQL query strings for comparison
        expected_sql = " ".join("""
            INSERT INTO trades (stockid, sellerid, buyerid, trade_date, price, quantity)
            VALUES (?, ?, ?, ?, ?, ?)
            """.split())
        actual_sql = " ".join(mock_modify.call_args[0][0].split())
        actual_params = mock_modify.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (stockid, sellerid, buyerid, trade_date, price, quantity))
        self.assertEqual(trade_id, mock_modify.return_value)


    @patch('stockmarket.modify')
    def test_update_order(self, mock_modify):
        """ Test for updating order
        """
        orderid = 1
        order_date = '2024-03-01'
        quantity = 150
        selling = 1
        price = 155.00

        update_order(orderid, order_date, quantity, selling, price)

        # Normalize the SQL query strings for comparison
        expected_sql = " ".join("""
            UPDATE orders
            SET order_date = ?, quantity = ?, selling = ?, price = ?
            WHERE orderid = ?
            """.split())
        actual_sql = " ".join(mock_modify.call_args[0][0].split())
        actual_params = mock_modify.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (order_date, quantity, selling, price, orderid))


    @patch('stockmarket.modify')
    def test_delete_order(self, mock_modify):
        """ Test for deleting order
        """
        orderid = 1
        delete_order(orderid)

        # Normalize the SQL query strings for comparison
        expected_sql = " ".join("""
            DELETE FROM orders
            WHERE orderid = ?
            """.split())
        actual_sql = " ".join(mock_modify.call_args[0][0].split())
        actual_params = mock_modify.call_args[0][1]

        # Asserts
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_params, (orderid,))


if __name__ == '__main__':
    unittest.main()