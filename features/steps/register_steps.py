from behave import given, when, then


@given('the user is on the registration page')
def given_user_on_registration_page(context):
    response = context.client.get('/registry')
    assert response.status_code == 200, "Couldn't reach registry page."


@when('the user submits a registration form with an existing username')
def when_user_submits_form_with_existing_username(context):
    form_data = {
        'first_name': 'Alex',
        'last_name': 'Tandori',
        'tradername': 'alex_t',
        'password': 'Pass123%'
    }
    response = context.client.post('/register', data=form_data, follow_redirects=True)
    assert response.status_code == 200, "Couldn't reach register."



@when('the user submits a registration form with invalid data')
def when_user_submits_form_with_invalid_data(context):
    form_data = {
        'first_name': '',
        'last_name': 'Doe',
        'tradername': 'newUser',
        'password': 'Pass123%'
    }
    response = context.client.post('/register', data=form_data, follow_redirects=True)
    assert response.status_code == 200, "Couldn't reach register."


@then('the user should see an error message about username uniqueness')
def then_user_sees_username_uniqueness_error(context):
    assert 'Please choose a different one.' in context.response.data.decode(), "Tradername error message wasn't displayed."


@then('the user should see an error message about invalid data')
def then_user_sees_invalid_data_error(context):
    assert 'First name is required.' in context.response.data.decode(), "First name error message wasn't displayed."
