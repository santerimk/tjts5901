Feature: User Logout
  As a logged-in user
  I want to log out of the application
  So that I can ensure my session is ended securely

  Scenario: Successful logout
    Given the user is logged in
    When the user requests to log out
    Then the user should be redirected to the login page
    And the user cannot access the dashboard page
