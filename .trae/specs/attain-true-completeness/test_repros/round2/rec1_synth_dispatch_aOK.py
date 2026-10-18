# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_dispatch_a.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F4a（item 11 try 体派发碰撞/andor 全链族，非语料）。'
def d_subscr_stmt(v, out):
    try:
        out.append((v and [v] or [0])[0])
        return None
    except IndexError:
        out.append(0)
        return None
def d_subscr_two(v, w, out):
    try:
        for i in range(2):
            if i:
                out.append((v and [v] or [0])[0])
                out.append((w and [w] or [0])[0])
    except ValueError:
        pass
    return out
