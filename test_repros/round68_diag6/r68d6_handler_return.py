def h1(x):
    try:
        f()
    except BaseException as e:
        return {'a': 1, 'b': 2}, x


def h2(x):
    try:
        f()
    except BaseException as e:
        return x


def h3(x):
    try:
        f()
    except BaseException:
        return {'a': 1, 'b': 2}, x
