Feature: User Login
  As a user
  I want to log in to the application
  So that I can access my dashboard

  Scenario: Successful login with valid credentials
    Given the user is on the login page
    When the user submits login form with valid credentials
    Then the user should be redirected to the dashboard

  Scenario: Unsuccessful login with invalid credentials
    Given the user is on the login page
    When the user submits login form with invalid credentials
    Then the user should see an error message

  Scenario: Attempt to login with empty credentials
    Given the user is on the login page
    When the user submits login form with empty username and password
    Then the user should see an error message regarding empty fields
