# Source Generated with Decompyle++ (Python version)
# File: r2v3_c05_control_and_form.pyc (Python 3.11)

def f(username, uinfo):
    if username in uinfo and not uinfo[username]:
        raise Exception('no user')
    return 1
