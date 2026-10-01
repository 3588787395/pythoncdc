# r2_13 except* 与普通 except 混用（同 try 混用非法，取嵌套形态）
# 焦点：except* 嵌套于普通 try/except 内（3.11 语法 `except* TypeError:`）


def f(mix):
    out = []
    try:
        try:
            if mix:
                raise ExceptionGroup("g", [TypeError("t")])
            raise ValueError("plain")
        except* TypeError as e:
            out.append("star")
    except ValueError:
        out.append("plain")
    return out


def g(mix):
    out = []
    try:
        if mix:
            raise ExceptionGroup("g", [TypeError("t"), OSError("o")])
        out.append("no-raise")
    except* TypeError as e:
        out.append("star-T")
    except* OSError as e:
        out.append("star-O")
    finally:
        out.append("fin")
    return out
