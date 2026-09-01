# Source Generated with Decompyle++ (Python version)
# File: repro_12_multi_kwonly_defaults.pyc (Python 3.11)

def f(*args, x=1, y=2, z=3):
    return sum(args) + x + y + z
result = f(10, 20, x=5)
