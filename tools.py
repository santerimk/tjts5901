from passlib.hash import bcrypt
import stockmarket as db


def verify_password(provided_password, hashword):
    """Verifies that the trader password matches with the stored hash.
    """
    verification_success = bcrypt.verify(provided_password, hashword)
    return verification_success


def hash_password(password):
    """Generates and returns a bcrypt-hash of the password.
    """
    hashed_password = bcrypt.hash(password)
    return hashed_password