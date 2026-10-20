# Source Generated with Decompyle++ (Python version)
# File: r6_synth_b140_nested_break.pyc (Python 3.11)

def s_b140_break_nested_loop(n):
    out = []
    for i in range(n):
        while i > 0:
            i -= 1
            try:
                out.append(i)
            except ValueError:
                break
        else:
            out.append('inner-done')
    return out
def s_b140_break_in_finally_loop(n):
    out = []
    for i in range(n):
        while i > 0:
            i -= 1
            try:
                out.append(i)
            finally:
                if i == 1:
                    pass
                break
                continue
    return out
