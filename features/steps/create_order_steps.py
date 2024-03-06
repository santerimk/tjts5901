from behave import given, when, then
from flask import url_for, session


@given('the user is logged in and on the order creation page')
def given_user_logged_in_and_on_order_creation_page(context):
    context.response = context.client.post('/auth', data={'tradername': 'alex_t', 'password': 'Pass123%'}, follow_redirects=True)
    context.response = context.client.get('/order_create?stockid=1&order_type=Bid')
    assert context.response.status_code == 200, "Order creation page not reachable."


@when('the user submits the order creation form with valid details for an offer')
def when_user_submits_valid_offer_details(context):
    session['trader']['1']
    form_data = {
        'hidden': '1',
        'quantity': '100',
        'type': 'Offer',
        'price': '10.00'
    }
    context.response = context.client.post('/order_place', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Reaching order_place failed."


@when('the user submits the order creation form with valid details for a bid')
def when_user_submits_valid_bid_details(context):
    session['trader']['2']
    form_data = {
        'hidden': '2',
        'quantity': '50',
        'type': 'Bid',
        'price': '20.00'
    }
    context.response = context.client.post('/order_place', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Reaching order_place failed."


@when('the user submits the order creation form with invalid details')
def when_user_submits_invalid_order_details(context):
    session['trader']['1']
    form_data = {
        'hidden': '1',
        'quantity': '-10',
        'type': 'Bid',
        'price': '10.00'
    }
    context.response = context.client.post('/order_place', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Reaching order_place failed."


@then('the order should be created successfully and the user should be redirected to the dashboard with a confirmation message')
def then_order_created_and_redirected_with_message(context):
    assert context.response.status_code == 200, "Response status code is not 200."
    assert url_for('dashboard') in context.response.request.url, "User not redirected to dashboard."
    assert 'New order was placed!' in context.response.data.decode() or 'Trade was made!' in context.response.data.decode(), "Confirmation message not shown."


@then('the user should see an error message regarding the invalid details')
def then_user_sees_error_message_invalid_details(context):
    assert 'Quantity must be greater than 0.' in context.response.data.decode(), "Error message not shown for invalid order details."
    