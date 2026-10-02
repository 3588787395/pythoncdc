def cr_list_call(xs):
    return list(x * 2 for x in xs)


def cr_tuple_call(xs):
    return tuple(x + 1 for x in xs)


def cr_set_call(xs):
    return set(x % 5 for x in xs)


def cr_sorted(xs):
    return sorted(x for x in xs)


def cr_any(xs):
    return any(x > 10 for x in xs)


def cr_all(xs):
    return all(x < 10 for x in xs)


def cr_dict_call(pairs):
    return dict((k, v) for k, v in pairs)


def cr_join(xs):
    return "/".join(str(x) for x in xs)
