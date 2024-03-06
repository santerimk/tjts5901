from behave import given, when, then


@given('the user is logged in and on the order creation page')
def given_user_logged_in_and_on_order_creation_page(context):
    context.response = context.client.post('/auth', data={'tradername': 'alex_t', 'password': 'Pass123%'}, follow_redirects=True)
    context.response = context.client.get('/order_create?stockid=1&order_type=Bid')
    assert context.response.status_code == 200, "Order creation page not reachable."


@when('the user submits the order creation form with valid details for an offer')
def when_user_submits_valid_offer_details(context):
    form_data = {
        'hidden': '1',
        'quantity': '100',
        'type': 'Offer',
        'price': '3310.00'
    }
    context.response = context.client.post('/order_place', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Reaching order_place failed."


@when('the user submits the order creation form with valid details for a bid')
def when_user_submits_valid_bid_details(context):
    form_data = {
        'hidden': '1',
        'quantity': '50',
        'type': 'Bid',
        'price': '3280.00'
    }
    context.response = context.client.post('/order_place', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Reaching order_place failed."


@when('the user submits the order creation form with invalid details')
def when_user_submits_invalid_order_details(context):
    form_data = {
        'hidden': '1',
        'quantity': '-10',
        'type': 'Bid',
        'price': '3320.00'
    }
    context.response = context.client.post('/order_place', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Reaching order_place failed."


@then('the order should be created with the user being redirected to the dashboard')
def then_order_created_and_redirected_to_dashboard(context):
    assert 'Welcome' in context.response.data.decode(), "User is not redirected to the dashboard."


@then('the user should see an error message regarding the invalid details')
def then_user_sees_error_message_invalid_details(context):
    assert 'Quantity must be greater than 0.' in context.response.data.decode(), "Error message not shown for invalid order details."
    