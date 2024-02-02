def add(a, b):
    """add"""
    return a + b

def subtract(a, b):
    """subs"""
    return a - b


def multiply(a, b):
    """mult"""
    return a * b


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(-1, -1) == -2

def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(-1, -1) == 0
    assert subtract(5, 2) == 3


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-1, 1) == -1
    assert multiply(-1, -1) == 1
