# Source Generated with Decompyle++ (Python version)
# File: repro_11_closure_cell.pyc (Python 3.11)

def make_adder(n):
    def adder(x):
        return x + n
    return adder
