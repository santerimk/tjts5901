"""Module providing a functions for testing."""

# A simple function to test add
def add(a, b):
    """add"""
    return a + b

# A simple function to test subs
def subtract(a, b):
    """subs"""
    return a - b

# A simple function to test mult
def multiply(a, b):
    """mult"""
    return a * b

# Test cases for add
def test_add():
    """test_add"""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(-1, -1) == -2

# Test cases for subs
def test_subtract():
    """test_subs"""
    assert subtract(10, 5) == 5
    assert subtract(-1, -1) == 0
    assert subtract(5, 2) == 3

# Test cases for subs
def test_multiply():
    """test_mult"""
    assert multiply(3, 4) == 12
    assert multiply(-1, 1) == -1
    assert multiply(-1, -1) == 1
