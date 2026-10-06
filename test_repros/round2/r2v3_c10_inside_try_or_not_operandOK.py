# Source Generated with Decompyle++ (Python version)
# File: r2v3_c10_inside_try_or_not_operand.pyc (Python 3.11)

def f(username, uinfo):
    try:
        if username not in uinfo or not uinfo[username]:
            raise Exception('no user')
    except Exception as e:
        log(e)
    return 1
