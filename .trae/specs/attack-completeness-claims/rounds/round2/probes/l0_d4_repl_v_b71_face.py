"""逐字复刻 v_b71_face（B142 登记残余所在文件）"""


def v_fin_else_continue(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                continue
            else:
                out.append(-r)
        out.append(r)
    return out


def v_nest_fin_continue(rows):
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                out.append(1)
        finally:
            out.append(2)
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
