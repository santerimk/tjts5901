Feature: User Registration
  As a new user
  I want to register an account
  So that I can use the trading platform

  Scenario: Successful registration with valid data
    Given the user is on the registration page
    When the user submits a registration form with valid data
    Then the user should be registered successfully

  Scenario: Unsuccessful registration with already existing username
    Given the user is on the registration page
    When the user submits a registration form with an existing username
    Then the user should see an error message about username uniqueness

  Scenario: Unsuccessful registration with invalid data
    Given the user is on the registration page
    When the user submits a registration form with invalid data
    Then the user should see an error message about invalid data
