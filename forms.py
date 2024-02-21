from wtforms import StringField, PasswordField, SubmitField, validators, ValidationError
from polyglot import PolyglotForm
import stockmarket as db
from tools import verify_password, hash_password



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
        results = db.query("SELECT hashword FROM traders WHERE tradername = ?", (field.data.strip(),), True)
        if not results or not results['hashword']:
            return
        if not verify_password(field.data, results['hashword']):
            raise ValidationError("Invalid password.")

    tradername = StringField("Tradername", validators=[check_if_exists])
    password = PasswordField("Password", validators=[verify])
    login = SubmitField("Login")