_tmp = []

def cleanup():
    for t in _tmp:
        try:
            print(t)
        except OSError:
            pass
    del _tmp[:]
    global _opener
    if _opener:
        _opener = None

_opener = None
