# Source Generated with Decompyle++ (Python version)
# File: repro_05_with_then_if_method_call.pyc (Python 3.11)

def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if b is not None:
        x = content.upper().strip()
    return x
