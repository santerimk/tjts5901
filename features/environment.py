from main import app
from stockmarket import reset_and_populate
from flask_wtf.csrf import CSRFProtect
import os


csrf = None  # Initialize CSRFProtect as None initially


def before_scenario(context, scenario):
    context.client = app.test_client()
    context.client.testing = True
    global csrf
    if not os.environ.get('FLASK_ENV') == 'testing':  # Only enable CSRF protection if not in testing mode
        csrf = CSRFProtect(app)


def after_scenario(context, scenario):
    reset_and_populate()