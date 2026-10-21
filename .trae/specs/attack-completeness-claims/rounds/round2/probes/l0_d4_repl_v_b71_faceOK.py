# Source Generated with Decompyle++ (Python version)
# File: l0_d4_repl_v_b71_face.pyc (Python 3.11)

__doc__ = '逐字复刻 v_b71_face（B142 登记残余所在文件）'
def v_fin_else_continue(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                continue
            out.append(-r)
        out.append(r)
    return out
def v_nest_fin_continue(rows):
    out = []
    for r in rows:
        try:
            if r == 0:
                try:
                    out.append(1)
                    out.append(1)
                finally:
                    out.append(2)
        finally:
            out.append(1)
        out.append(r)
    return out
def n_fin_noctrl(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                out.append(-r)
        out.append(r)
    return out
