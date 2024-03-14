import os
from dotenv import load_dotenv
import unittest
import sqlite3
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import requests_mock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from stockmarket import get_stock

load_dotenv()


class BidOrders(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.base_url = "http://127.0.0.1:5000"  # Adjust to your application's URL

    def login(self):
        username = os.getenv('TEST_USERNAME1')
        password = os.getenv('TEST_PASSWORD1')
        self.driver.get(self.base_url + "/login")
        username_field = self.driver.find_element(By.NAME, "tradername")
        username_field.send_keys(username)
        password_field = self.driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        submit_button = self.driver.find_element(By.NAME, "login")
        submit_button.click()
    

    @requests_mock.Mocker()
    def test_bid_price_validation(self, mock):
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 1.08, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.login()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Bid")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("15")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))  # M1 x 1.08
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        # This may involve checking for a success message or verifying the order appears in the order listing
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("New order was placed!", success_message.text)

    @requests_mock.Mocker()
    def test_bid_price_rejection(self, mock):
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 1.11, 1)  # Test price exceeding 1.11 times the last traded price

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.login()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Bid")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("15")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))  # Test price exceeding 1.11 times the last traded price
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was rejected
        # This may involve checking for a rejection message or verifying the order does not appear in the order listing
        rejection_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error2"))  # Adjust to your application's rejection message ID
        )
        self.assertIn("Price must be within 10% of the last traded price.", rejection_message.text)


    # tearDown and remove entries from the database
    def tearDown(self):
        connection = sqlite3.connect('stockmarket.db')
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(orderid) FROM ORDERS')
        latest_id = cursor.fetchone()[0]
        cursor.execute('DELETE FROM ORDERS WHERE orderid = ?', (latest_id,))

        connection.commit()
        connection.close()
        self.driver.quit()
        

class OfferOrders(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.base_url = "http://127.0.0.1:5000"  # Adjust to your application's URL

    def login(self):
        username = os.getenv('TEST_USERNAME1')
        password = os.getenv('TEST_PASSWORD1')
        self.driver.get(self.base_url + "/login")
        username_field = self.driver.find_element(By.NAME, "tradername")
        username_field.send_keys(username)
        password_field = self.driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        submit_button = self.driver.find_element(By.NAME, "login")
        submit_button.click()    
    

    @requests_mock.Mocker()
    def test_offer_price_validation(self, mock):
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 0.905, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.login()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Offer")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("15")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))  # M1 x 0.9
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        # This may involve checking for a success message or verifying the order appears in the order listing
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("New order was placed!", success_message.text)

    @requests_mock.Mocker()
    def test_offer_price_rejection(self, mock):
        # Mock the AAPL price API response
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 1.11, 1)  # Test price exceeding 1.11 times the last traded price

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.login()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Offer")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("15")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))  # Test price exceeding 1.11 times the last traded price
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was rejected
        # This may involve checking for a rejection message or verifying the order does not appear in the order listing
        rejection_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error2"))  # Adjust to your application's rejection message ID
        )
        self.assertIn("Price must be within 10% of the last traded price.", rejection_message.text)


    # tearDown and remove entries from the database
    def tearDown(self):
        connection = sqlite3.connect('stockmarket.db')
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(orderid) FROM ORDERS')
        latest_id = cursor.fetchone()[0]
        cursor.execute('DELETE FROM ORDERS WHERE orderid = ?', (latest_id,))
        connection.commit()
        connection.close()
        self.driver.quit()




class TradeInputValidationTest(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.base_url = "http://127.0.0.1:5000"  # Adjust to your application's URL
        self.login()
    
    def login(self):
        username = os.getenv('TEST_USERNAME1')
        password = os.getenv('TEST_PASSWORD1')
        self.driver.get(self.base_url + "/login")
        username_field = self.driver.find_element(By.NAME, "tradername")
        username_field.send_keys(username)
        password_field = self.driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        submit_button = self.driver.find_element(By.NAME, "login")
        submit_button.click()

    def submit_order(self, stock_id, order_type, quantity, price):
        self.driver.get(self.base_url + f"/order_create?stockid={stock_id}&order_type={order_type}")
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys(str(quantity))
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(price))
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()

    def verify_order_rejection(self, expected_message):
        rejection_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error2"))
        )
        self.assertIn(expected_message, rejection_message.text)


    def test_bid_order_zero_quantity_rejected(self):
        test_price = self.fetch_test_price()
        self.submit_order(stock_id=1, order_type="Bid", quantity=0, price=test_price)
        self.verify_order_rejection("Quantity must be greater than 0.")

    '''
    def test_bid_order_fractional_quantity_rejected(self):
        test_price = self.fetch_test_price()
        self.submit_order(stock_id=1, order_type="Bid", quantity="10.1", price=test_price)
        self.verify_order_rejection("Please enter a valid value.")
    '''

    def test_offer_order_negative_quantity_rejected(self):
        test_price = self.fetch_test_price()
        self.submit_order(stock_id=1, order_type="Offer", quantity="-100", price=test_price)
        self.verify_order_rejection("Quantity must be greater than 0.")
    
    def fetch_test_price(self):
        # Fetch the last traded price from the database
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db, 2)
        return test_price
    

    def tearDown(self):
        self.driver.quit()

        
class TradeExecutionTest(unittest.TestCase):
    
    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.base_url = "http://127.0.0.1:5000"  # Adjust to your application's URL
    
    def loginfirsttrader(self):
        username = os.getenv('TEST_USERNAME1')
        password = os.getenv('TEST_PASSWORD1')
        self.driver.get(self.base_url + "/login")
        username_field = self.driver.find_element(By.NAME, "tradername")
        username_field.send_keys(username)
        password_field = self.driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        submit_button = self.driver.find_element(By.NAME, "login")
        submit_button.click()

    def loginsecondtrader(self):
        username = os.getenv('TEST_USERNAME2')
        password = os.getenv('TEST_PASSWORD2')
        self.driver.get(self.base_url + "/login")
        username_field = self.driver.find_element(By.NAME, "tradername")
        username_field.send_keys(username)
        password_field = self.driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        submit_button = self.driver.find_element(By.NAME, "login")
        submit_button.click()

    def fetch_test_price(self):
        # Fetch the last traded price from the database
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db, 2)
        return test_price
    
    
    @requests_mock.Mocker()
    def test_firstbid_price_validation(self, mock):
        """Test the offer price validation by submitting a bid order and verifying the acceptance of the order.
        """
        # Mock the API response
        mock.get("http://yourapi.com/api/price", json={'price': 100})

        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.loginfirsttrader()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Bid")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("100")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        # This may involve checking for a success message or verifying the order appears in the order listing
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("New order was placed!", success_message.text)


    @requests_mock.Mocker()
    def test_firstoffer_price_validation(self, mock):
        """Test the offer price validation by submitting a bid order with a calculated test price.
        """
        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 0.8, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.loginsecondtrader()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Offer")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("200")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))  # M1 x 0.8
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was rejected
        # This may involve checking for a rejection message or verifying the order does not appear in the order listing
        rejection_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error2"))  # Adjust to your application's rejection message ID
        )
        self.assertIn("Price must be within 10% of the last traded price.", rejection_message.text)


    @requests_mock.Mocker()
    def test_secondbid_price_validation(self, mock):
        """Test the offer price validation by submitting a bid order and verifying the acceptance of the order.
        """
        # Mock the API response
        mock.get("http://yourapi.com/api/price", json={'price': 100})

        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 1.01, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.loginfirsttrader()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Bid")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("200")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        # This may involve checking for a success message or verifying the order appears in the order listing
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("New order was placed!", success_message.text)


    @requests_mock.Mocker()
    def test_thirdbid_price_validation(self, mock):
        """Test the offer price validation by submitting a bid order and verifying the acceptance of the order.
        """
        # Mock the API response
        mock.get("http://yourapi.com/api/price", json={'price': 100})

        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db * 0.95, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.loginfirsttrader()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Bid")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("50")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        # This may involve checking for a success message or verifying the order appears in the order listing
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("New order was placed!", success_message.text)


    @requests_mock.Mocker()
    def test_fourthbid_price_validation(self, mock):
        """Test the offer price validation by submitting a bid order and verifying the acceptance of the order.
        """
        # Mock the API response
        mock.get("http://yourapi.com/api/price", json={'price': 100})

        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.loginfirsttrader()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Bid")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("30")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        # This may involve checking for a success message or verifying the order appears in the order listing
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("New order was placed!", success_message.text)


    @requests_mock.Mocker()
    def test_secondoffer_price_validation(self, mock):
        """
        Test the validation of the second offer price.
        """
        # Mock the API response
        mock.get("http://yourapi.com/api/price", json={'price': 100})

        stock_id = 1
        stock_details = get_stock(stock_id)
        last_traded_price_db = stock_details['last_traded_price']
        test_price = round(last_traded_price_db, 1)

        self.driver.get(self.base_url + "/login")
        # Perform login if necessary
        self.loginsecondtrader()
    
        # Navigate to the order submission page and submit a bid order
        self.driver.get(self.base_url + "/order_create?stockid=1&order_type=Offer")  # Adjust URL and parameters as necessary
        
        # Assume form fields have IDs 'quantity' and 'price'
        quantity_field = self.driver.find_element(By.NAME, "quantity")
        quantity_field.clear()
        quantity_field.send_keys("250")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys(str(test_price))
        
        submit_button = self.driver.find_element(By.NAME, "order")
        submit_button.click()
        
        # Verify the order was accepted
        success_message = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info1"))
        )
        self.assertIn("Trade was made!", success_message.text)

    def tearDown(self):
        self.driver.quit()


if __name__ == "__main__":
    unittest.main()
