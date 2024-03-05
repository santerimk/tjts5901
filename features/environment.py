from main import app
from stockmarket import reset_and_populate


def before_scenario(context, scenario):
    context.client = app.test_client()
    context.client.testing = True


def after_scenario(context, scenario):
    reset_and_populate()