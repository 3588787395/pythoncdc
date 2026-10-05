# Source Generated with Decompyle++ (Python version)
# File: rv3_03_b85_b86_func_domain.pyc (Python 3.11)

import os as _os
def chain_assign():
    a = b = c = {'k': 1}
    d = e = [1, 2, 3]
    f = g = h = a
    return (a, b, c, d, e, f, g, h)
def multi_with(p):
    r1 = None
    with open(p, 'w') as fa:
        with open(p + '.bak', 'w') as fb:
            fa.write('x')
            fb.write('y')
            r1 = fa
            r2 = fb
    with _os.popen('echo hi') as fc, _os.popen('echo yo') as fd:
        r1 = fc.readline()
        r2 = fd.readline()
    return (r1, r2)
