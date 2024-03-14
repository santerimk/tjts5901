from behave import given, when, then


@given('the user is logged in')
def given_user_is_logged_in(context):
    context.response = context.client.post('/auth', data={'tradername': 'alex_t', 'password': 'Pass123%'}, follow_redirects=True)
    assert context.response.status_code == 200, "Failed to log in for the scenario."


@when('the user requests to log out')
def when_user_requests_to_log_out(context):
    context.response = context.client.get('/logout', follow_redirects=True)
    assert context.response.status_code == 200, "Logout failed."


@then('the user should be redirected to the login page')
def then_user_redirected_to_login_page(context):
    assert 'login' in context.response.data.decode().lower(), "User is not redirected to login page."


@then('the user cannot access the dashboard page')
def then_user_cannot_access_dashboard(context):
    context.response = context.client.get('/dashboard', follow_redirects=True)
    assert 'login' in context.response.data.decode().lower(), "User was able to access dashboard."
