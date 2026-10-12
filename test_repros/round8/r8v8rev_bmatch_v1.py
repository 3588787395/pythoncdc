def v1(x, g, sink):
    # B77/B81/B103: guard 后跟多语句体（守卫 + 体装配域）
    r = 0
    match x:
        case 1 if g:
            r = 1
            sink.append(r)
        case _:
            r = 2
    return r


