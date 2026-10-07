# Source Generated with Decompyle++ (Python version)
# File: r6_g3_chainexit_ctl.pyc (Python 3.11)

def r6_g3_chainexit_ctl(limit, key, table):
    while limit > 0:
        if key in table and key == table:
            continue
        if key != table and key in table:
            continue
        use(key)
        limit = limit - 1
