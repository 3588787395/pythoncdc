# Source Generated with Decompyle++ (Python version)
# File: r2_09_finally_mixed_boolop.pyc (Python 3.11)

def f(a, b, c, log):
    try:
        log.append(a)
    finally:
        if a and b or c:
            log.append('T')
        log.append('F-done')
    return log
def g(a, b, c, acc):
    try:
        acc.append('try')
    finally:
        if a and b or c:
            acc.append('loop')
            while False:
                pass
        if a:
            if b:
                if c:
                    assert False, 'r2_09'
        if not b:
            pass
        if not c:
            pass
        assert False, 'r2_09'
    return acc
