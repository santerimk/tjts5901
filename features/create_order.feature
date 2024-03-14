Feature: Creating Stock Order
  As a logged-in user
  I want to create a stock order
  So that I can offer or bid on stocks

  Scenario: Successful creation of a stock offer
    Given the user is logged in and on the order creation page
    When the user submits the order creation form with valid details for an offer
    Then the order should be created with the user being redirected to the dashboard

  Scenario: Successful creation of a stock bid
    Given the user is logged in and on the order creation page
    When the user submits the order creation form with valid details for a bid
    Then the order should be created with the user being redirected to the dashboard

  Scenario: Unsuccessful creation of a stock order with invalid details
    Given the user is logged in and on the order creation page
    When the user submits the order creation form with invalid details
    Then the user should see an error message regarding the invalid details
