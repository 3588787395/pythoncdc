# Source Generated with Decompyle++ (Python version)
# File: l0_a3_triple_nested_finally_continue.pyc (Python 3.11)

__doc__ = 'AT-02/B142: for x try/finally x try/finally —— 两级 finally 副本 + continue'
def a3(xs):
    for x in xs:
        try:
            if x:
                try:
                    print('inner-fin')
                    print('inner-fin')
                finally:
                    print('outer-fin')
        finally:
            print('inner-fin')
