# Source Generated with Decompyle++ (Python version)
# File: r2v3_c13_and_not_operand_control.pyc (Python 3.11)

def f(username, uinfo):
    if username in uinfo and uinfo[username]:
        return 1
    raise Exception('no user')
