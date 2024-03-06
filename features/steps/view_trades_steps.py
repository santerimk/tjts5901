from behave import given, when, then
import stockmarket as db


@given('the user is logged in and on the dashboard')
def given_user_logged_in_and_on_dashboard(context):
    db.add_trade('1', '1', '2', '2024-12-21 07:14:53', '120.56', '17')
    context.response = context.client.post('/auth', data={'tradername': 'alex_t', 'password': 'Pass123%'}, follow_redirects=True)
    context.response = context.client.get('/dashboard')
    assert context.response.status_code == 200, "Couldn't log in and reach dashboard."


@when('the user navigates to the trade listings page')
def when_user_navigates_to_trade_listings_page(context):
    context.response = context.client.get('/trade_listing', follow_redirects=True)
    assert context.response.status_code == 200, "Trade listings page not reachable."


@then('the user should see a list of all available trades')
def then_user_sees_list_of_trades(context):
    assert '120.56' in context.response.data.decode(), "Trade listings not displayed."
