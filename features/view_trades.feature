Feature: Viewing Trade Listings
  As a logged-in user
  I want to view all available trades
  So that I can make informed trading decisions

  Scenario: Viewing available trades
    Given the user is logged in and on the dashboard
    When the user navigates to the trade listings page
    Then the user should see a list of all available trades
