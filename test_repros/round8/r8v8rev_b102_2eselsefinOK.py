# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_b102_2eselsefin.pyc (Python 3.11)

def v1(a, b, e, f):
    out = []
    try:
        out.append(a())
    except* ValueError:
        out.append('ve')
    except* TypeError:
        out.append('te')
    else:
        out.append('ok')
    finally:
        out.append('done')
    return out
def v2(a, b, e, f):
    out = []
    def inner():
        r = 0
        try:
            r = a() + b()
        except* ValueError:
            r = 1
        except* KeyError:
            r = 2
        else:
            out.append('ok')
        finally:
            out.append('fin')
        return r
    out.append(inner())
    return out
