from passlib.hash import bcrypt


def verify_password(provided_password, hashword):
    """Verifies that the provided password matches with the stored
    bcrypt-hashed password.
    """
    verification_success = bcrypt.verify(provided_password, hashword)
    return verification_success


def hash_password(password):
    """Generates and returns a bcrypt hash of the provided password.
    """
    hashed_password = bcrypt.hash(password)
    return hashed_password
