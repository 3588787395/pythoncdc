# rv8_02: B55-c 判据面变体攻击 —— 空段 try/finally 尾随非 None 常量 return / with 体 try/finally / 循环内链式赋值
# 判据边界：_b55_is_pure_const_return_block「任意常量值」+ post-try 窄门控在
# with 宿主、else 分支、非尾随 return 形态下的不误收（False Positive 攻击）。


def tryfin_return_str():
    try:
        pass
    finally:
        pass
    return 'done'


def tryfin_return_negative():
    try:
        pass
    finally:
        pass
    return -42


def tryfin_then_more(x):
    try:
        pass
    finally:
        pass
    y = x + 1
    return y


def with_body_tryfin_chain(p):
    with open(p) as fh:
        try:
            pass
        finally:
            pass
    return fh


def try_except_fin_nonempty(x):
    try:
        v = int(x)
    except ValueError:
        v = 0
    finally:
        v = v + 1
    return v


def while_chain_subscript(xs, n):
    out = {}
    i = 0
    while i < n:
        out[i] = out['last'] = xs[i]
        i += 1
    return out
