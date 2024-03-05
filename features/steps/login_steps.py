from behave import given, when, then


@given('the user is on the login page')
def given_user_on_login_page(context):
    context.response = context.client.get('/login')
    assert context.response.status_code == 200, "Couldn't reach login page."


@when('the user submits login form with valid credentials')
def when_user_submits_valid_credentials(context):
    form_data = {'tradername': 'alex_t', 'password': 'Pass123%'}
    context.response = context.client.post('/auth', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Couldn't reach auth page."


@when('the user submits login form with invalid credentials')
def when_user_submits_invalid_credentials(context):
    form_data = {'tradername': 'alex_t', 'password': 'pass123%'}
    context.response = context.client.post('/auth', data=form_data, follow_redirects=True)
    assert context.response.status_code == 200, "Couldn't reach auth page."


@when('the user submits login form with empty username and password')
def when_user_submits_empty_credentials(context):
    context.response = context.client.post('/auth', data={'tradername': '', 'password': ''}, follow_redirects=True)
    assert context.response.status_code == 200, "Couldn't reach auth page."


@then('the user should be redirected to the dashboard')
def then_user_redirected_to_dashboard(context):
    assert 'Welcome' in context.response.data.decode(), "User is not redirected to the dashboard."


@then('the user should see an error message')
def then_user_sees_error_message_invalid(context):
    assert 'Invalid password.' in context.response.data.decode(), "Password error message is not displayed"


@then('the user should see an error message regarding empty fields')
def then_user_sees_error_message_empty_fields(context):
    assert 'Tradername is required.' in context.response.data.decode(), "Tradername error message is not displayed."
