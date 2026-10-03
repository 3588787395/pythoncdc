"""R8 negative control 1: simplest return / single assign forms (must MATCH)."""


def n8_ret_const():
    return 1


def n8_ret_name(x):
    return x


def n8_single_assign():
    a = 5
    return a
