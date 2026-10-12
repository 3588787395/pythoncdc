def v1(a, b, e, f):
    # B102: 双 except* + else + finally 混合变体（非空 try 体）
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
    # B102: 双 except* + else + finally + 嵌套调用宿主（深一档组合）
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
