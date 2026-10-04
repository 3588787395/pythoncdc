# Source Generated with Decompyle++ (Python version)
# File: v_b74_face.pyc (Python 3.11)

__doc__ = 'rv2 变体面 B74（r10_06 case 体首 if 邻域）：末 case / 中间 case / 真 guard'
def v_case_if_last(x, flag):
    match x:
        case 1:
            return 'one'
        case _:
            if flag:
                return 'yes'
            else:
                return 'no'
def v_case_if_mid(x, flag):
    match x:
        case 1:
            if flag:
                return 'one-yes'
            else:
                return 'one-no'
        case 2:
            return 'two'
        case _:
            return 'other'
def n_true_guard(x, flag):
    match x:
        case 1:
            if flag:
                return 'one'
            else:
                return 'other'
        case _:
            pass
