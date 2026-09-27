# Source Generated with Decompyle++ (Python version)
# File: t05_continue_then_shared_tail.pyc (Python 3.11)

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
