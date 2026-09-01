# Source Generated with Decompyle++ (Python version)
# File: repro_03_kwonly_only.pyc (Python 3.11)

def f(*, kw1, kw2=5):
    return kw1 + kw2
result = f(kw1=1)
