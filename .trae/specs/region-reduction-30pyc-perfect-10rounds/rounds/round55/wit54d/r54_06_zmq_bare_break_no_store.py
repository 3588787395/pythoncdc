def w(g, first_address):
    address = g(1)
    try:
        message = g(2)
    except BaseException:
        got = False
        address = g(3)
        while first_address != address:
            try:
                message = g(4)
                break
            except Exception as e:
                address = g(5)
        if not got:
            return (None, 1)
    return message
