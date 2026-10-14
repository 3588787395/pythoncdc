# Source Generated with Decompyle++ (Python version)
# File: s5_b130_shapeA_ifmerge_is_trytail.pyc (Python 3.11)

def f5(cond):
    a = 0
    try:
        if cond:
            a = 1
            print(a)
        else:
            print('err')
        print('tail')
    except Exception as e:
        print(e)
    finally:
        print('fin')
    return a
