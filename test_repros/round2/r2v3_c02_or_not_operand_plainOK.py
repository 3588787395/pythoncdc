# Source Generated with Decompyle++ (Python version)
# File: r2v3_c02_or_not_operand_plain.pyc (Python 3.11)

def f(username, uinfo):
    if username not in uinfo or not uinfo[username]:
        raise Exception('no user')
    return 1
