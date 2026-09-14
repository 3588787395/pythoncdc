# Source Generated with Decompyle++ (Python version)
# File: m11_nested_for_deep_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        for b in a:
            for c in b:
                if c:
                    continue
        log.info('deep')
        return a
