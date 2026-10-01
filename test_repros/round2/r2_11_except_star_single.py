# r2_11 except* 异常组（单 except*）
# 焦点：3.11 PEP 654 —— CHECK_EG_MATCH/PREP_RERAISE_STAR 全链（台账 §7）


def f(tag):
    out = [tag]
    try:
        raise ExceptionGroup("g", [TypeError("bad"), ValueError("v")])
    except* TypeError:
        out.append("type")
    out.append("after")
    return out
