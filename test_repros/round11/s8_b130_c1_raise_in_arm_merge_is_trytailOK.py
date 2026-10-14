# Source Generated with Decompyle++ (Python version)
# File: s8_b130_c1_raise_in_arm_merge_is_trytail.pyc (Python 3.11)

def f9(cond, x, tail=0):
    try:
        if cond:
            if x == 0:
                raise ValueError('zero')
            tail = 1
            print('then')
        else:
            print('err')
        print('tail')
    except Exception as e:
        print(e)
    finally:
        print('fin')
    return tail
