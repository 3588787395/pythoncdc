# t06: t05 carried inside try/except (original loop sits in a protected range)
def t06(flag, items, write_info):
    try:
        for it in items:
            if flag:
                if it[0] == 'delete':
                    it[2] = '2'
                    continue
                log(it[0])
            write_info.append(it)
        return write_info
    except Exception:
        return None


def log(*a):
    return None
