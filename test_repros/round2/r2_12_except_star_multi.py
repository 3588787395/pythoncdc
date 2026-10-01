# r2_12 except* 异常组（多 except* 链）
# 焦点：except* 多 handler 链（region_analyzer.py:10424-10483 多 handler 归并）


def f(n):
    out = []
    try:
        if n == 0:
            raise ExceptionGroup("g", [TypeError("t"), ValueError("v"), KeyError("k")])
        out.append(n)
    except* TypeError as e:
        out.append("T")
    except* ValueError:
        out.append("V")
    except* KeyError as e:
        out.append("K")
    return out
