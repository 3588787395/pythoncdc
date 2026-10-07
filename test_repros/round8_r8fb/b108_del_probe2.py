def e04_asvar(x):
    try:
        g()
    except E as e:
        log(e)
    return x


def e05_asvar_ret(x):
    try:
        g()
    except E as e:
        return 0
