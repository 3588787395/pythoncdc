def w(g, first_address):
    address = g(1)
    try:
        message = g(2)
    except BaseException:
        _connec = False
        address = g(3)
        while first_address != address:
            try:
                message = g(4)
                _connec = True
                break
            except Exception as e:
                address = g(5)
        if not _connec:
            return (None, 1)
    return message
