from wtforms import StringField, PasswordField, SubmitField, ValidationError, RadioField, IntegerField, DecimalField, HiddenField, BooleanField
from wtforms.validators import InputRequired
from polyglot import PolyglotForm
import stockmarket as db
from tools import verify_password, get_stock



class RegistryForm(PolyglotForm):
    """Class for a registry form.
    """
    def require_first_name(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("First name is required.")

    def require_last_name(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("Last name is required.")

    def check_uniqueness(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("Tradername is required.")
        all_comparables = [comparable.strip().lower() for comparable, in db.query("SELECT tradername FROM traders")]
        tradername = field.data.strip().lower()
        if tradername in all_comparables:
            raise ValidationError(f'Tradername "{tradername.capitalize()}" already exists. Please choose a different one.')

    def check_complexity(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("Password is required.")
        password = field.data
        if ' ' in password:
            raise ValidationError("Password must not contain spaces.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must include at least one number.")
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must include at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise ValidationError("Password must include at least one lowercase letter.")
        if not any(char in set('!@#$%^&*()-_=+[]{};:,.<>?') for char in password):
            raise ValidationError("Password must include at least one special character.")

    def check_match(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("Password confirmation is required.")
        if field.data != self.password.data:
            raise ValidationError("Passwords must match.")

    first_name = StringField("First Name", validators=[require_first_name])
    last_name = StringField("Last Name", validators=[require_last_name])
    tradername = StringField("Tradername", validators=[check_uniqueness])
    password = PasswordField("Password", validators=[check_complexity])
    password_confirm = PasswordField("Confirm Password", validators=[check_match])
    register = SubmitField("Register")
    cancel = SubmitField("Cancel")



class LoginForm(PolyglotForm):
    """Class for a login form.
    """
    def check_if_exists(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("Tradername is required.")
        results = db.query("SELECT traderid FROM traders WHERE tradername = ?", (field.data.strip(),), True)
        if not results or not results['traderid']:
            raise ValidationError("Invalid tradername.")
    
    def verify(self, field):
        if not field.data or not field.data.strip():
            raise ValidationError("Password is required.")
        results = db.query("SELECT hashword FROM traders WHERE tradername = ?", (self.tradername.data.strip(),), True)
        if not results or not results['hashword']:
            return
        if not verify_password(field.data, results['hashword']):
            raise ValidationError("Invalid password.")

    tradername = StringField("Tradername", validators=[check_if_exists])
    password = PasswordField("Password", validators=[verify])
    login = SubmitField("Login")



class CreateOrderForm(PolyglotForm):
    """Class for a stock order creation form.
    """    
    def check_price(self, field):
        value = field.data
        if not str(value).replace('-', '', 1).replace(',', '.', 1).replace('.', '', 1).isdigit():
            raise ValidationError("Price must be a decimal number.")
        if value <= 0:
            raise ValidationError("Price must be greater than 0.")
        if not float(value * 100).is_integer():
            raise ValidationError("Price must not have more than 2 decimal places.")  
        stockid = int(self.hidden.data)
        stock = get_stock(stockid)
        last_traded_price = stock['last_traded_price']
        print(type(last_traded_price))
        min_limit = last_traded_price * 0.9
        max_limit = last_traded_price * 1.1
        if not (min_limit <= value <= max_limit):
            print(type(last_traded_price))
            raise ValidationError(f"Price must be within 10% of the last traded price.")

    def check_quantity(self, field):
        try:
            value = field.data
            if value <= 0:
                raise ValidationError("Quantity must be greater than 0.")
        except TypeError:
            return

    type = RadioField("Order Type", choices=["Bid", "Offer"], default="Bid", validators=[InputRequired()])
    price = DecimalField("Price (€)", default=1.00, validators=[check_price])
    quantity = IntegerField("Quantity", default=1, validators=[check_quantity])
    order = SubmitField("Place Order")
    cancel = SubmitField("Cancel")
    hidden = HiddenField()



class ModifyOrderForm(PolyglotForm):
    """Class for a stock order modification form.
    """    
    def check_price(self, field):
        value = field.data
        if not str(value).replace('-', '', 1).replace(',', '.', 1).replace('.', '', 1).isdigit():
            raise ValidationError("Price must be a decimal number.")
        if value <= 0:
            raise ValidationError("Price must be greater than 0.")
        if not float(value * 100).is_integer():
            raise ValidationError("Price must not have more than 2 decimal places.")  
        stockid = int(self.hidden1.data)
        stock = get_stock(stockid)
        last_traded_price = stock['last_traded_price']
        print(type(last_traded_price))
        min_limit = last_traded_price * 0.9
        max_limit = last_traded_price * 1.1
        if not (min_limit <= value <= max_limit):
            print(type(last_traded_price))
            raise ValidationError(f"Price must be within 10% of the last traded price.")

    def check_quantity(self, field):
        try:
            value = field.data
            if value <= 0:
                raise ValidationError("Quantity must be greater than 0.")
        except TypeError:
            return

    type = RadioField("Order Type", choices=["Bid", "Offer"], default="Bid", validators=[InputRequired()])
    price = DecimalField("Price (€)", default=1.00, validators=[check_price])
    quantity = IntegerField("Quantity", default=1, validators=[check_quantity])
    delete = BooleanField("Delete Order", default=False)
    order = SubmitField("Modify Order")
    cancel = SubmitField("Cancel")
    hidden1 = HiddenField()
    hidden2 = HiddenField()