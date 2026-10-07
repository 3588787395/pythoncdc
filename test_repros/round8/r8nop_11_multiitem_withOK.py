# Source Generated with Decompyle++ (Python version)
# File: r8nop_11_multiitem_with.pyc (Python 3.11)

def n8p11(a):
    with open(a) as fp:
        with open(a + '.tmp') as fq:
            r = fp.read()
            w = fq.write(r)
    return w
