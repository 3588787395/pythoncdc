def r6_g3_chainexit_ctl(limit, key, table):
    while limit > 0:
        if key in table:
            if key == table:
                continue
        if key != table:
            if key in table:
                continue
        use(key)
        limit = limit - 1
