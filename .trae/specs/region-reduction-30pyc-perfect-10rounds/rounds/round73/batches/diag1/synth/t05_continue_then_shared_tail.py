# t05: minimal - loop + if with a continue inside its then-arm + shared tail
# after the if (the tail is the only statement left before the back-edge).
def t05(flag, items, write_info):
    for it in items:
        if flag:
            if it[0] == 'delete':
                it[2] = '2'
                continue
            log(it[0])
        write_info.append(it)


def log(*a):
    return None
