# Source Generated with Decompyle++ (Python version)
# File: l0_e13_proj_for_match_with.pyc (Python 3.11)

__doc__ = 'AT-02 for x match 变量分离 3/3: case 体含 with（a2 的 with 子投影在 match 内）'
def e13(v):
    for x in v:
        match x:
            case 0 if x == 0:
                with open('f') as fh:
                    print(fh)
                pass
                continue
            case _:
                print('other')
