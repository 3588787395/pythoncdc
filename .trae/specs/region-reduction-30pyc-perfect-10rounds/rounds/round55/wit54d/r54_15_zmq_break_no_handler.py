def w(g, first_address):
    address = g(1)
    _connec = False
    m = None
    while first_address != address:
        try:
            m = g(2)
            _connec = True
            break
        except Exception as e:
            address = g(3)
    if not _connec:
        return 1
    return m
