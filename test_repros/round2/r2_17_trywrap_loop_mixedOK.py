# Source Generated with Decompyle++ (Python version)
# File: r2_17_trywrap_loop_mixed.pyc (Python 3.11)

def f(a, b, c, out):
    for i in range(3):
        try:
            if a and b or c:
                out.append(i)
                break
            elif a or b and c:
                out.append(i * 2)
                while False:
                    pass
        except TypeError:
            out.append('e')
def g(a, b, c, out):
    while a:
        try:
            if a and b or c:
                out.append(1)
                break
        except TypeError:
            out.append('e')
        a = False
    return out
