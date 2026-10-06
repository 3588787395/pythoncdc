# Source Generated with Decompyle++ (Python version)
# File: r2v3_c04_control_explicit_not_or.pyc (Python 3.11)

def f(username, uinfo):
    if not (username not in uinfo or uinfo[username]):
        raise Exception('no user')
    return 1
