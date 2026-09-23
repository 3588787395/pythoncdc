def ctl_elif_all_return(a, b):
    if a:
        return 1
    elif b:
        return 2
    else:
        return 3


def ctl_if_return_then_if(a, b):
    if a:
        return 1
    if b:
        x = 2
    else:
        x = 3
    return x


def ctl_if_return_else_nested(a, b):
    if a:
        return 1
    else:
        if b:
            return 2
        return 3


def ctl_ternary_after_return(a, b):
    if a is None:
        return 0
    y = 'p' if b else 'q'
    return y


def ctl_chain_compare(a, b):
    if 0 < a < 10:
        return 1
    if b:
        return 2
    return 3


def ctl_raise_then_cond(a, b):
    if a:
        raise ValueError('x')
    if b:
        return 2
    return 3


def ctl_return_and_or_head(a, b):
    if a and b:
        return 1
    if a or b:
        return 2
    return 3


def ctl_nested_ternary_in_if(a, b):
    if a:
        return 'x' if b else 'y'
    if b:
        return 'z'
    return 'w'
