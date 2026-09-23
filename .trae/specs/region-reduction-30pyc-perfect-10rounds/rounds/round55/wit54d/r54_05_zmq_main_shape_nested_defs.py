def _helper(g, n):
    address = g(n)
    return address


def w(g, first_address):
    address = _helper(g, 1)
    try:
        message = _helper(g, 2)
    except BaseException:
        _connect = False
        address = _helper(g, 3)
        while first_address != address:
            try:
                message = _helper(g, 4)
                _connect = True
                break
            except BaseException:
                address = _helper(g, 5)
        if not _connect:
            return (None, 1)
    return message
