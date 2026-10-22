# Source Generated with Decompyle++ (Python version)
# File: c10_decorator_chain.pyc (Python 3.11)

def deco_a(f):
    def inner(*a, **k):
        return ('a', f(*a, **(k)))
    return inner
def deco_b(f):
    def inner(*a, **k):
        return ('b', f(*a, **(k)))
    return inner
@deco_a
@deco_b
def g(x):
    return x
def main():
    print(g(1))
