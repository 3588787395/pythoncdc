# Source Generated with Decompyle++ (Python version)
# File: t06_try_continue_shared_tail.pyc (Python 3.11)

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
