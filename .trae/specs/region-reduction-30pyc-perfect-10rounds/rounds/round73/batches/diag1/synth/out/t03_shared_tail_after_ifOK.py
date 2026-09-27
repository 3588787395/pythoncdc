# Source Generated with Decompyle++ (Python version)
# File: t03_shared_tail_after_if.pyc (Python 3.11)

def t03(flag, items, write_info):
    if flag:
        if items[0] == 'start':
            items[2] = '0'
        if items[0] == 'stop':
            items[2] = '1'
        if items[0] == 'delete':
            items[2] = '2'
        log(items[0])
    write_info.append(items)
    return write_info
def log(*a):
    return None
