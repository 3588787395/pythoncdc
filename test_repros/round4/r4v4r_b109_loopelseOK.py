# Source Generated with Decompyle++ (Python version)
# File: r4v4r_b109_loopelse.pyc (Python 3.11)

class CL2:
    def m(self, xs):
        while xs:
            y = xs.pop()
            if y > 3:
                break
        else:
            return None
        return y
class CL3:
    def m(self, xs, flag):
        for x in xs:
            if flag:
                break
        else:
            return None
        return x
def normal_while(xs):
    i = 0
    while i < len(xs):
        i += 1
    return None
def for_else_ctrl(xs):
    for x in xs:
        if x:
            break
    else:
        return 0
    return x
def while_else_not_returnnone(xs):
    n = 0
    while xs:
        if n > 3:
            break
        n += 1
    else:
        n = -1
    return n
def nested_loop_else(xs):
    for x in xs:
        while x:
            if x > 2:
                break
            x -= 1
        if x:
            break
    else:
        return 0
    return x
