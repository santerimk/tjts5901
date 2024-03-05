from main import app
from stockmarket import reset_and_populate
import os

def before_all(context):
    os.environ['FLASK_ENV'] = 'testing'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection in testing mode

def before_scenario(context, scenario):
    context.client = app.test_client()
    context.client.testing = True

def after_scenario(context, scenario):
    reset_and_populate()