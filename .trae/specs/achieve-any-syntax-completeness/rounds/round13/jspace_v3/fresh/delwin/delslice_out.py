# Source Generated with Decompyle++ (Python version)
# File: delslice.pyc (Python 3.11)

global _opener
_tmp = []
def cleanup():
    global _opener
    for t in _tmp:
        try:
            print(t)
        except OSError:
            pass
    if _opener:
        _opener = None
    else:
        return None
_opener = None
