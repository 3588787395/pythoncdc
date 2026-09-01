# Source Generated with Decompyle++ (Python version)
# File: repro_10_r10_except_handler.pyc (Python 3.11)

def r10_except_handler(self, k):
    try:
        return self.d[k]
        return None
    except KeyError:
        self.d[k] = (r := make())
        return r
def make():
    return 5
